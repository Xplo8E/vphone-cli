## com.apple.kec.corecrypto

> `com.apple.kec.corecrypto`

```diff

-1922.80.7.0.0
-  __TEXT.__cstring: 0x4dba
-  __TEXT.__const: 0x19770
+1922.101.2.0.0
+  __TEXT.__cstring: 0x4c81
+  __TEXT.__const: 0x196e0
   __TEXT.__fips_hmacs: 0x20
-  __TEXT_EXEC.__text: 0x6b69c
+  __TEXT_EXEC.__text: 0x69c7c
   __TEXT_EXEC.__auth_stubs: 0x0
   __DATA.__data: 0x9340
   __DATA.__bss: 0x29e0

   __DATA_CONST.__got: 0x10
   __DATA_CONST.__auth_ptr: 0x178
   __DATA_CONST.__const: 0x3fc8
-  UUID: 4EB81262-2BA1-3D00-804A-F3C2D2C39DCA
-  Functions: 1827
-  Symbols:   2355
-  CStrings:  469
+  UUID: 0B130D5E-A8AB-3ADF-ABDB-B66594F61D4F
+  Functions: 1847
+  Symbols:   2375
+  CStrings:  463
 
Symbols:
+ _OUTLINED_FUNCTION_9
+ _cc_dunit_type
+ _ccec_sign_composite_hedged
+ _ccmlkem_decompress_coefficient
+ _ccmlkem_kem_keypair_from_seed_unchecked
+ _ccmlkem_ntt_basemul_cache_compute
+ _ccshake256_internal
+ _ccxof_absorb_internal
+ _ccxof_squeeze_internal
- _ccmlkem_ntt_basemul
- _fipspost_post_integrity_l4
- _fipspost_post_tdes_ecb
CStrings:
- "FIPSPOST_KEXT [%llu] %s:%d: FAILED: des3_ecb_decrypt cmp\n"
- "FIPSPOST_KEXT [%llu] %s:%d: FAILED: des3_ecb_decrypt one_shot\n"
- "FIPSPOST_KEXT [%llu] %s:%d: FAILED: fipspost_post_tdes_ecb: %d\n"
- "FIPSPOST_KEXT [%llu] %s:%d: PASSED: (%u ms) - fipspost_post_tdes_ecb\n"
- "fipspost_post_integrity_l4"
- "fipspost_post_tdes_ecb_decrypt"

```
