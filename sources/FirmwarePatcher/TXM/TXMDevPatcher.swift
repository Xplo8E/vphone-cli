// TXMDevPatcher.swift — Dev-variant TXM patcher (entitlements, debugger, developer mode).
//
// Historical note: derived from the legacy Python firmware patcher during the Swift migration.

import Foundation

/// Dev-variant patcher for TXM images.
///
/// Adds 5 patch methods (11 patch records) beyond base trustcache bypass:
///   1. selector24 force PASS (mov w0, #0xa1 + b epilogue)
///   2. get-task-allow entitlement BL → mov x0, #1
///   3. selector42|29 shellcode hook + manifest flag force
///   4. debugger entitlement BL → mov w0, #1
///   5. developer-mode guard → nop
public final class TXMDevPatcher: TXMPatcher {
    private lazy var machOSegments: [MachOSegmentInfo] = MachOParser.parseSegments(from: buffer.data)

    override public func findAll() throws -> [PatchRecord] {
        patches = []
        try patchTrustcacheBypass() // base patch
        patchSelector24ForcePass()
        patchGetTaskAllowForceTrue()
        patchSelector42_29Shellcode()
        patchDebuggerEntitlementForceTrue()
        patchDeveloperModeBypass()
        return patches
    }

    // MARK: - ADRP+ADD string reference search

    /// Convert a file offset to the address model used by ADRP.
    ///
    /// Older TXM payloads were treated as flat binaries, where file offset and
    /// execution address are equivalent. iOS 18 TXM is a Mach-O, so ADRP resolves
    /// against segment VM addresses while patches are still emitted by file offset.
    private func fileOffsetToAddress(_ offset: Int) -> UInt64? {
        guard offset >= 0, offset < buffer.count else { return nil }

        guard !machOSegments.isEmpty else {
            return UInt64(offset)
        }

        for segment in machOSegments {
            let start = Int(segment.fileOffset)
            let end = start + Int(segment.fileSize)
            if offset >= start, offset < end {
                return segment.vmAddr + UInt64(offset - start)
            }
        }
        return nil
    }

    private func decodeADRPPage(raw: UInt32, instructionAddress: UInt64) -> UInt64 {
        let immlo = (raw >> 29) & 0x3
        let immhi = (raw >> 5) & 0x7FFFF
        let imm21 = (immhi << 2) | immlo
        let signedImm21 = Int64(Int32(bitPattern: imm21 << 11) >> 11)
        let delta = signedImm21 << 12
        let pcPage = instructionAddress & ~UInt64(0xFFF)

        if delta >= 0 {
            return pcPage &+ UInt64(delta)
        }
        return pcPage &- UInt64(-delta)
    }

    private func decodeADRAddress(raw: UInt32, instructionAddress: UInt64) -> UInt64 {
        let immlo = (raw >> 29) & 0x3
        let immhi = (raw >> 5) & 0x7FFFF
        let imm21 = (immhi << 2) | immlo
        let signedImm21 = Int64(Int32(bitPattern: imm21 << 11) >> 11)

        if signedImm21 >= 0 {
            return instructionAddress &+ UInt64(signedImm21)
        }
        return instructionAddress &- UInt64(-signedImm21)
    }

    /// Find all ADR/ADRP references that resolve to the address of `targetOff`.
    /// Returns an array of `(adrpOff, addOff)` file-offset pairs.
    ///
    /// The tuple names stay compatible with the old ADRP+ADD caller contract.
    /// For direct ADR references, both offsets are the ADR instruction offset.
    private func findRefsToOffset(_ targetOff: Int) -> [(adrpOff: Int, addOff: Int)] {
        guard let targetAddress = fileOffsetToAddress(targetOff) else { return [] }
        let targetPage = targetAddress & ~UInt64(0xFFF)
        let pageOff = UInt32(targetAddress & 0xFFF)

        let size = buffer.count
        var refs: [(Int, Int)] = []
        var off = 0
        while off + 4 <= size {
            let rawA = buffer.readU32(at: off)
            guard let instructionAddress = fileOffsetToAddress(off) else { off += 4; continue }

            // ADR: direct +/-1 MiB PC-relative address. iOS 18 TXM uses this
            // for many cstring references because __TEXT_EXEC and __TEXT are
            // close enough in the Mach-O address map.
            if rawA & 0x9F00_0000 == 0x1000_0000 {
                if decodeADRAddress(raw: rawA, instructionAddress: instructionAddress) == targetAddress {
                    refs.append((off, off))
                }
                off += 4
                continue
            }

            // ADRP: bits[31]=1, bits[28:24]=10000
            guard rawA & 0x9F00_0000 == 0x9000_0000 else { off += 4; continue }

            let adrpPage = decodeADRPPage(raw: rawA, instructionAddress: instructionAddress)
            guard adrpPage == targetPage else { off += 4; continue }

            let adrpRd = rawA & 0x1F

            // The ADD is usually adjacent, but allow a short instruction window
            // because newer TXM builds can interleave setup moves between ADRP
            // and ADD.
            for delta in stride(from: 4, through: 32, by: 4) {
                let addOff = off + delta
                guard addOff + 4 <= size else { break }
                let rawB = buffer.readU32(at: addOff)

                // ADD immediate (64-bit, no shift): bits[31:23] = 100100010.
                guard rawB & 0xFF80_0000 == 0x9100_0000 else { continue }
                guard ((rawB >> 22) & 0x1) == 0 else { continue }

                let addRn = (rawB >> 5) & 0x1F
                let addImm12 = (rawB >> 10) & 0xFFF
                guard adrpRd == addRn, addImm12 == pageOff else { continue }

                refs.append((off, addOff))
                break
            }
            off += 4
        }
        return refs
    }

    /// Find all ADRP+ADD instruction pairs referencing any occurrence of `needle` in the binary.
    ///
    /// Returns `(stringOff, adrpOff, addOff)` tuples — mirrors Python `_find_string_refs`.
    private func findStringRefs(_ needle: Data) -> [(stringOff: Int, adrpOff: Int, addOff: Int)] {
        var results: [(Int, Int, Int)] = []
        var seen = Set<Int>()
        var search = 0
        while let range = buffer.data.range(of: needle, in: search ..< buffer.count) {
            let sOff = range.lowerBound
            search = sOff + 1
            for (adrpOff, addOff) in findRefsToOffset(sOff) {
                if !seen.contains(adrpOff) {
                    seen.insert(adrpOff)
                    results.append((sOff, adrpOff, addOff))
                }
            }
        }
        return results
    }

    /// Find string refs using a UTF-8 string literal.
    private func findStringRefs(_ needle: String) -> [(stringOff: Int, adrpOff: Int, addOff: Int)] {
        guard let data = needle.data(using: .utf8) else { return [] }
        return findStringRefs(data)
    }

    // MARK: - Helpers

    /// Scan backward from `off` for PACIBSP — mirrors Python `_find_func_start`.
    private func findFuncStart(_ off: Int, back: Int = 0x1000) -> Int? {
        let start = max(0, off - back)
        var scan = off & ~3
        while scan >= start {
            if buffer.readU32(at: scan) == ARM64.pacibspU32 {
                return scan
            }
            scan -= 4
        }
        return nil
    }

    /// Find a zero-filled cave of at least `minInsns * 4` bytes — mirrors Python `_find_udf_cave`.
    ///
    /// The Python logic:
    ///   - Scan forward for a run of zero words.
    ///   - Prefer a run immediately after a branch instruction (with 8-byte safety pad).
    ///   - Otherwise, return the nearest run to `nearOff`.
    private func findUdfCave(minInsns: Int, nearOff: Int? = nil, maxDistance: Int = 0x80000) -> Int? {
        let need = minInsns * 4
        let size = buffer.count
        let searchStart = nearOff.map { max(0, $0 - 0x1000) } ?? 0
        let searchEnd = nearOff.map { min(size, $0 + maxDistance) } ?? size

        var best: Int? = nil
        var bestDist = Int.max
        var off = searchStart

        let branchMnemonics: Set = ["b", "b.eq", "b.ne", "b.lo", "b.hs", "cbz", "cbnz", "tbz", "tbnz"]

        while off < searchEnd {
            // Count consecutive zero words starting at off
            var run = off
            while run < searchEnd, buffer.readU32(at: run) == 0 {
                run += 4
            }

            if run - off >= need {
                // Check instruction before the run
                if off >= 4, let prev = disasm.disassembleOne(in: buffer.data, at: off - 4) {
                    if branchMnemonics.contains(prev.mnemonic) {
                        // 2-word safety gap after the preceding branch
                        let padded = off + 8
                        return (padded + need <= run) ? padded : off
                    }
                }
                // Not after a branch — track nearest to nearOff
                if let near = nearOff {
                    let dist = abs(off - near)
                    if dist < bestDist {
                        best = off
                        bestDist = dist
                    }
                }
            }

            off = (run > off) ? run + 4 : off + 4
        }
        return best
    }

    /// Find the function start of the debugger-gate function containing the
    /// `com.apple.private.cs.debugger` BL site — mirrors Python `_find_debugger_gate_func_start`.
    ///
    /// Pattern (at BL site):
    ///   [scan-8] mov x0, #0
    ///   [scan-4] mov x2, #0
    ///   [scan+0] bl  <entitlement_check>
    ///   [scan+4] tbnz w0, #0, <...>
    private func findDebuggerGateFuncStart() -> Int? {
        let refs = findStringRefs(Data("com.apple.private.cs.debugger".utf8))
        var starts = Set<Int>()

        for (_, _, addOff) in refs {
            let scanEnd = min(addOff + 0x20, buffer.count - 8)
            var scan = addOff
            while scan < scanEnd {
                guard
                    let i = disasm.disassembleOne(in: buffer.data, at: scan),
                    let n = disasm.disassembleOne(in: buffer.data, at: scan + 4),
                    scan >= 8,
                    let p1 = disasm.disassembleOne(in: buffer.data, at: scan - 4),
                    let p2 = disasm.disassembleOne(in: buffer.data, at: scan - 8)
                else { scan += 4; continue }

                let tbnzOk = n.mnemonic == "tbnz" && n.operandString.hasPrefix("w0, #0,")
                let p1ok = p1.mnemonic == "mov" && p1.operandString == "x2, #0"
                let p2ok = p2.mnemonic == "mov" && p2.operandString == "x0, #0"

                if i.mnemonic == "bl", tbnzOk, p1ok, p2ok {
                    if let fs = findFuncStart(scan) {
                        starts.insert(fs)
                    }
                }
                scan += 4
            }
        }

        guard starts.count == 1 else { return nil }
        return starts.first
    }

    private func decodeConditionalBranchTarget(insn: UInt32, pc: Int) -> Int? {
        // B.cond: imm19:5, target = pc + sign_extend(imm19:'00')
        if insn & 0xFF00_0010 == 0x5400_0000 {
            let imm19 = (insn >> 5) & 0x7FFFF
            let signedImm = Int32(bitPattern: imm19 << 13) >> 13
            return pc + Int(signedImm) * 4
        }

        // CBZ/CBNZ: imm19:5. Match both 32-bit and 64-bit forms.
        if insn & 0x7E00_0000 == 0x3400_0000 {
            let imm19 = (insn >> 5) & 0x7FFFF
            let signedImm = Int32(bitPattern: imm19 << 13) >> 13
            return pc + Int(signedImm) * 4
        }

        // TBZ/TBNZ: imm14:5. Match both branch polarities/register widths.
        if insn & 0x7E00_0000 == 0x3600_0000 {
            let imm14 = (insn >> 5) & 0x3FFF
            let signedImm = Int32(bitPattern: imm14 << 18) >> 18
            return pc + Int(signedImm) * 4
        }

        return nil
    }

    // MARK: - Dev Patches

    /// Patch selector24 handler to return 0xA1 (PASS) immediately.
    ///
    /// Inserts `mov w0, #0xa1 ; b <epilogue>` right after the prologue,
    /// skipping validation while preserving the stack frame.
    func patchSelector24ForcePass() {
        let size = buffer.count

        // Scan for any `mov w0, #0xa1` in the binary
        var off = 0
        while off + 4 <= size {
            guard let ins = disasm.disassembleOne(in: buffer.data, at: off),
                  ins.mnemonic == "mov", ins.operandString == "w0, #0xa1"
            else { off += 4; continue }

            guard let funcStart = findFuncStart(off) else { off += 4; continue }

            // Verify this is selector24 by searching for the characteristic
            // LDR X1,[Xn,#0x38] / ADD X2,... / BL / LDP pattern in [funcStart, off)
            var patternFound = false
            var scan = funcStart
            while scan + 12 < off {
                guard
                    let i0 = disasm.disassembleOne(in: buffer.data, at: scan),
                    let i1 = disasm.disassembleOne(in: buffer.data, at: scan + 4),
                    let i2 = disasm.disassembleOne(in: buffer.data, at: scan + 8),
                    let i3 = disasm.disassembleOne(in: buffer.data, at: scan + 12)
                else { scan += 4; continue }

                let ldrOk = i0.mnemonic == "ldr"
                    && i0.operandString.contains("x1,")
                    && i0.operandString.contains("#0x38]")
                let addOk = i1.mnemonic == "add" && i1.operandString.hasPrefix("x2,")
                let blOk = i2.mnemonic == "bl"
                let ldpOk = i3.mnemonic == "ldp"

                if ldrOk, addOk, blOk, ldpOk {
                    patternFound = true
                    break
                }
                scan += 4
            }

            guard patternFound else { off += 4; continue }

            // Find prologue end: scan for `add x29, sp, #imm`
            var bodyStart: Int? = nil
            var p = funcStart + 4
            while p < funcStart + 0x30 {
                if let pi = disasm.disassembleOne(in: buffer.data, at: p),
                   pi.mnemonic == "add", pi.operandString.hasPrefix("x29, sp,")
                {
                    bodyStart = p + 4
                    break
                }
                p += 4
            }

            guard let body = bodyStart else {
                log("  [-] TXM: selector24 prologue end not found")
                return
            }

            // Find epilogue: scan forward from `off` for retab/ret,
            // then walk back for `ldp x29, x30, ...`
            var epilogue: Int? = nil
            var r = off
            while r < min(off + 0x200, size) {
                if let ri = disasm.disassembleOne(in: buffer.data, at: r),
                   ri.mnemonic == "retab" || ri.mnemonic == "ret"
                {
                    var e = r - 4
                    while e > max(r - 0x20, funcStart) {
                        if let ei = disasm.disassembleOne(in: buffer.data, at: e),
                           ei.mnemonic == "ldp", ei.operandString.contains("x29, x30")
                        {
                            epilogue = e
                            break
                        }
                        e -= 4
                    }
                    break
                }
                r += 4
            }

            guard let epilogueOff = epilogue else {
                log("  [-] TXM: selector24 epilogue not found")
                return
            }

            emit(body, ARM64.movW0_0xA1,
                 patchID: "txm_dev.selector24_bypass_mov",
                 description: "selector24 bypass: mov w0, #0xa1 (PASS)")

            guard let bInsn = ARM64Encoder.encodeB(from: body + 4, to: epilogueOff) else {
                log("  [-] TXM: selector24 branch encoding failed")
                return
            }
            emit(body + 4, bInsn,
                 patchID: "txm_dev.selector24_bypass_b",
                 description: "selector24 bypass: b epilogue")
            return
        }

        log("  [-] TXM: selector24 handler not found")
    }

    /// Force get-task-allow entitlement check to return true (BL → mov x0, #1).
    func patchGetTaskAllowForceTrue() {
        let refs = findStringRefs(Data("get-task-allow".utf8))
        guard !refs.isEmpty else {
            log("  [-] TXM: get-task-allow string refs not found")
            return
        }

        var cands: [Int] = []
        for (_, _, addOff) in refs {
            let scanEnd = min(addOff + 0x20, buffer.count - 4)
            var scan = addOff
            while scan < scanEnd {
                guard
                    let i = disasm.disassembleOne(in: buffer.data, at: scan),
                    let n = disasm.disassembleOne(in: buffer.data, at: scan + 4)
                else { scan += 4; continue }

                if i.mnemonic == "bl",
                   n.mnemonic == "tbnz",
                   n.operandString.hasPrefix("w0, #0,")
                {
                    cands.append(scan)
                }
                scan += 4
            }
        }

        guard cands.count == 1 else {
            log("  [-] TXM: expected 1 get-task-allow BL site, found \(cands.count)")
            return
        }

        emit(cands[0], ARM64.movX0_1,
             patchID: "txm_dev.get_task_allow",
             description: "get-task-allow: bl -> mov x0,#1")
    }

    /// Selector 42|29 patch via dynamic cave shellcode + branch redirect.
    ///
    /// Shellcode (6 instructions in a zero-filled cave):
    ///   nop                    (safety padding)
    ///   mov x0, #1
    ///   strb w0, [x20, #0x30]
    ///   mov x0, x20
    ///   b   <stub_off + 4>     (return to original flow)
    func patchSelector42_29Shellcode() {
        guard let fn = findDebuggerGateFuncStart() else {
            log("  [-] TXM: debugger-gate function not found (selector42|29)")
            return
        }

        // Find the stub: bti j; mov x0,x20; bl <fn>; mov x1,x21; mov x2,x22; bl <fn>; b ...
        var stubs: [Int] = []
        let size = buffer.count

        var off = 4
        while off + 24 <= size {
            guard
                let p = disasm.disassembleOne(in: buffer.data, at: off - 4),
                let i0 = disasm.disassembleOne(in: buffer.data, at: off),
                let i1 = disasm.disassembleOne(in: buffer.data, at: off + 4),
                let i2 = disasm.disassembleOne(in: buffer.data, at: off + 8),
                let i3 = disasm.disassembleOne(in: buffer.data, at: off + 12),
                let i4 = disasm.disassembleOne(in: buffer.data, at: off + 16),
                let i5 = disasm.disassembleOne(in: buffer.data, at: off + 20)
            else { off += 4; continue }

            guard p.mnemonic == "bti", p.operandString == "j" else { off += 4; continue }
            guard i0.mnemonic == "mov", i0.operandString == "x0, x20" else { off += 4; continue }
            guard i1.mnemonic == "bl" else { off += 4; continue }
            guard i2.mnemonic == "mov", i2.operandString == "x1, x21" else { off += 4; continue }
            guard i3.mnemonic == "mov", i3.operandString == "x2, x22" else { off += 4; continue }
            guard i4.mnemonic == "bl" else { off += 4; continue }
            guard i5.mnemonic == "b" else { off += 4; continue }

            // i4's branch target must point to fn (the debugger-gate function)
            let i4u32 = buffer.readU32(at: off + 16)
            if let tgt = ARM64Encoder.decodeBranchTarget(insn: i4u32, pc: UInt64(off + 16)),
               Int(tgt) == fn
            {
                stubs.append(off)
            }
            off += 4
        }

        guard stubs.count == 1 else {
            log("  [-] TXM: selector42|29 stub expected 1, found \(stubs.count)")
            return
        }
        let stubOff = stubs[0]

        guard let cave = findUdfCave(minInsns: 6, nearOff: stubOff) else {
            log("  [-] TXM: no UDF cave found for selector42|29 shellcode")
            return
        }

        // Redirect stub entry to shellcode cave
        guard let branchToShellcode = ARM64Encoder.encodeB(from: stubOff, to: cave) else {
            log("  [-] TXM: selector42|29 branch-to-cave encoding failed")
            return
        }
        emit(stubOff, branchToShellcode,
             patchID: "txm_dev.sel42_29_branch",
             description: "selector42|29: branch to shellcode")

        // Shellcode body at cave
        emit(cave, ARM64.nop, patchID: "txm_dev.sel42_29_shell_nop", description: "selector42|29 shellcode pad: udf -> nop")
        emit(cave + 4, ARM64.movX0_1, patchID: "txm_dev.sel42_29_shell_mov1", description: "selector42|29 shellcode: mov x0,#1")
        emit(cave + 8, ARM64.strbW0X20_30, patchID: "txm_dev.sel42_29_shell_strb", description: "selector42|29 shellcode: strb w0,[x20,#0x30]")
        emit(cave + 12, ARM64.movX0X20, patchID: "txm_dev.sel42_29_shell_mov20", description: "selector42|29 shellcode: mov x0,x20")

        // Branch back to stub_off + 4 (skip the redirected first instruction)
        guard let branchBack = ARM64Encoder.encodeB(from: cave + 16, to: stubOff + 4) else {
            log("  [-] TXM: selector42|29 branch-back encoding failed")
            return
        }
        emit(cave + 16, branchBack,
             patchID: "txm_dev.sel42_29_shell_ret",
             description: "selector42|29 shellcode: branch back")
    }

    /// Force debugger entitlement check to return true (BL → mov w0, #1).
    ///
    /// Pattern (at BL site):
    ///   [scan-8] mov x0, #0
    ///   [scan-4] mov x2, #0
    ///   [scan+0] bl  <entitlement_check>
    ///   [scan+4] tbnz w0, #0, <...>
    func patchDebuggerEntitlementForceTrue() {
        let refs = findStringRefs(Data("com.apple.private.cs.debugger".utf8))
        guard !refs.isEmpty else {
            log("  [-] TXM: debugger refs not found")
            return
        }

        var cands: [Int] = []
        for (_, _, addOff) in refs {
            let scanEnd = min(addOff + 0x20, buffer.count - 4)
            var scan = addOff
            while scan < scanEnd {
                guard
                    scan >= 8,
                    let i = disasm.disassembleOne(in: buffer.data, at: scan),
                    let n = disasm.disassembleOne(in: buffer.data, at: scan + 4),
                    let p1 = disasm.disassembleOne(in: buffer.data, at: scan - 4),
                    let p2 = disasm.disassembleOne(in: buffer.data, at: scan - 8)
                else { scan += 4; continue }

                if i.mnemonic == "bl",
                   n.mnemonic == "tbnz",
                   n.operandString.hasPrefix("w0, #0,"),
                   p1.mnemonic == "mov", p1.operandString == "x2, #0",
                   p2.mnemonic == "mov", p2.operandString == "x0, #0"
                {
                    cands.append(scan)
                }
                scan += 4
            }
        }

        guard cands.count == 1 else {
            log("  [-] TXM: expected 1 debugger BL site, found \(cands.count)")
            return
        }

        emit(cands[0], ARM64.movW0_1,
             patchID: "txm_dev.debugger_entitlement",
             description: "debugger entitlement: bl -> mov w0,#1")
    }

    /// Developer-mode bypass: NOP conditional guard before deny log path.
    ///
    /// Finds `tbz/tbnz/cbz/cbnz w9, #0, <...>` just before the
    /// "developer mode enabled due to system policy configuration" string ref,
    /// then NOPs it.
    func patchDeveloperModeBypass() {
        let needle = "developer mode enabled due to system policy configuration"
        let refs = findStringRefs(Data(needle.utf8))
        guard !refs.isEmpty else {
            log("  [-] TXM: developer-mode string ref not found")
            return
        }

        let guardMnemonics: Set = ["tbz", "tbnz", "cbz", "cbnz"]
        var cands: [(off: Int, patch: Data, description: String)] = []
        var seen = Set<Int>()

        for (_, _, addOff) in refs {
            // Find the force-enable assignment immediately before the log string.
            var forceOff: Int? = nil
            var scan = addOff - 4
            while scan >= max(addOff - 0x20, 0) {
                if let ins = disasm.disassembleOne(in: buffer.data, at: scan),
                   ins.mnemonic == "mov",
                   ins.operandString == "w19, #1" || ins.operandString == "w20, #1"
                {
                    forceOff = scan
                    break
                }
                scan -= 4
            }
            guard let forceOff else { continue }

            let funcStart = findFuncStart(addOff) ?? max(forceOff - 0x100, 0)
            var back = forceOff - 4
            while back >= max(funcStart, forceOff - 0x100) {
                defer { back -= 4 }
                guard let ins = disasm.disassembleOne(in: buffer.data, at: back),
                      guardMnemonics.contains(ins.mnemonic)
                else { continue }

                // Legacy shape:
                //   tbnz w9, #0, normal_path
                //   mov  w20, #1
                // NOPing the guard forces fall-through into the force-enable block.
                if back + 4 == forceOff,
                   ins.mnemonic == "tbz" || ins.mnemonic == "tbnz",
                   ins.operandString.hasPrefix("w9, #0,"),
                   seen.insert(back).inserted
                {
                    cands.append((
                        off: back,
                        patch: ARM64.nop,
                        description: "developer mode bypass: legacy guard -> nop"
                    ))
                    continue
                }

                // iOS 18.5 shape:
                //   cbz w9, force_enable
                //   ... normal policy path ...
                // force_enable:
                //   mov w19, #1
                // Replacing the conditional branch with unconditional B reaches
                // the same force-enable block regardless of the policy byte.
                let raw = buffer.readU32(at: back)
                guard decodeConditionalBranchTarget(insn: raw, pc: back) == forceOff,
                      let branch = ARM64Encoder.encodeB(from: back, to: forceOff),
                      seen.insert(back).inserted
                else { continue }

                cands.append((
                    off: back,
                    patch: branch,
                    description: "developer mode bypass: conditional branch -> force-enable branch"
                ))
            }
        }

        guard cands.count == 1 else {
            log("  [-] TXM: expected 1 developer mode guard, found \(cands.count)")
            return
        }

        emit(cands[0].off, cands[0].patch,
             patchID: "txm_dev.developer_mode_bypass",
             description: cands[0].description)
    }
}
