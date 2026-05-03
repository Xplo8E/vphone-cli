## libxpc.dylib

> `/usr/lib/system/libxpc.dylib`

```diff

-3089.80.10.0.0
-  __TEXT.__text: 0x44718
-  __TEXT.__auth_stubs: 0x12f0
+3102.100.102.0.0
+  __TEXT.__text: 0x43a78
+  __TEXT.__auth_stubs: 0x1300
   __TEXT.__delay_stubs: 0x140
   __TEXT.__delay_helper: 0x148
   __TEXT.__objc_methlist: 0x374
-  __TEXT.__const: 0x650
-  __TEXT.__cstring: 0x7f51
-  __TEXT.__oslogstring: 0x3186
+  __TEXT.__const: 0x630
+  __TEXT.__cstring: 0x80cb
+  __TEXT.__oslogstring: 0x318a
   __TEXT.__dof_libxpc: 0xa5d
-  __TEXT.__unwind_info: 0x13f8
+  __TEXT.__unwind_info: 0x1458
   __TEXT.__objc_classname: 0x243
   __TEXT.__objc_methname: 0x1e2
   __TEXT.__objc_methtype: 0xb5

   __DATA_CONST.__objc_imageinfo: 0x8
   __DATA_CONST.__objc_selrefs: 0x100
   __DATA_CONST.__objc_superrefs: 0x58
-  __AUTH_CONST.__auth_got: 0x9a8
+  __AUTH_CONST.__auth_got: 0x9b0
   __AUTH_CONST.__const: 0x2618
   __AUTH_CONST.__objc_const: 0x2338
   __AUTH.__objc_data: 0x50
   __DATA.__data: 0xcfc
   __DATA.__crash_info: 0x148
-  __DATA.__common: 0x10
   __DATA.__bss: 0xa0
   __DATA_DIRTY.__objc_data: 0xaf0
   __DATA_DIRTY.__data: 0x4
-  __DATA_DIRTY.__common: 0x8
-  __DATA_DIRTY.__bss: 0xf8
+  __DATA_DIRTY.__bss: 0xe0
   - /System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation
   - /System/Library/PrivateFrameworks/XPCSupport.framework/Versions/A/XPCSupport
   - /usr/lib/libobjc.A.dylib

   - /usr/lib/system/libsystem_sandbox.dylib
   - /usr/lib/system/libsystem_trace.dylib
   - /usr/lib/system/libunwind.dylib
-  UUID: 3B264F68-2825-3790-8796-4B49581D6425
-  Functions: 1951
-  Symbols:   3193
-  CStrings:  1414
+  UUID: 618039C8-9965-3782-A7D2-90FD4C3DD66F
+  Functions: 1972
+  Symbols:   3229
+  CStrings:  1424
 
Symbols:
+ _OUTLINED_FUNCTION_6
+ _OUTLINED_FUNCTION_7
+ __MergedGlobals
+ ___launch_domain_routine_async_block_invoke.56
+ ___launch_domain_routine_async_block_invoke.61
+ ___launch_domain_routine_async_block_invoke.61.cold.1
+ ___launch_service_monitor_removal_port_block_invoke.51
+ __block_descriptor_tmp.127
+ __block_descriptor_tmp.135
+ __block_literal_global.129
+ __block_literal_global.137
+ __copy_key_from_plist
+ __cryptex_prefix_paths
+ __current_version
+ __ios_support_version
+ __os_log_debug_impl
+ __os_system_version_initialize
+ __sim_current_host_version
+ __trim_trailing_slashes
+ __xpc_connection_derive_connection_port
+ __xpc_connection_init_recv_port
+ __xpc_pipe_derive_port
+ __xpc_resolve_real_path
+ __xpc_session_fault
+ _audit_session_port
+ _current_dyld_version.0
+ _current_dyld_version.1
+ _launch_get_user_context
+ _normalize_cryptex_path.cold.1
+ _os_transaction_xref_dispose.cold.1
+ _os_transaction_xref_dispose.cold.2
+ _xpc_connection_copy_attrs.cold.1
+ _xpc_connection_derive_connection_port.cold.1
+ _xpc_connection_derive_connection_port.cold.2
+ _xpc_connection_derive_connection_port.cold.3
+ _xpc_pipe_derive_port.cold.1
+ _xpc_pipe_derive_port.cold.2
+ _xpc_session_dispose.cold.3
+ _xpc_session_dispose.cold.4
+ os_transaction_create.cold.1
+ os_transaction_create.cold.2
+ xpc_service_set_attach_handler.cold.2
+ xpc_service_set_attach_handler.cold.3
- ___launch_domain_routine_async_block_invoke.52
- ___launch_domain_routine_async_block_invoke.57
- ___launch_domain_routine_async_block_invoke.57.cold.1
- ___launch_service_monitor_removal_port_block_invoke.47
- ___xpc_session_setup_connection_handlers_block_invoke.cold.8
- __block_descriptor_tmp.130
- __block_descriptor_tmp.42
- __block_descriptor_tmp.51
- __block_descriptor_tmp.56
- __block_literal_global.132
- __os_once
- __system_ios_support_version_copy_string_sysctl
- __system_ios_support_version_fallback
- __system_version_copy_string_plist
- __system_version_copy_string_sysctl
- __system_version_fallback
- __system_version_parse_string
- __system_version_plist_path
- __xpc_assert_dumping_ground
- __xpc_plist_parse_date
- _availability_version_check.cold.1
- _availability_version_check.cold.2
- _current_host_version
- _current_ios_support_version
- _current_version
- _der_vm_CEType_from_ccder_tag
- _launchd_service_instance_create_request.cold.1
- _parsed_host_version
- _parsed_ios_support_version
- _parsed_version
- _populate_current_host_version
- _populate_current_ios_support_version
- _populate_current_version
- _xpc_connection_init_send_port.cold.1
- _xpc_connection_init_send_port.cold.2
- _xpc_connection_init_send_port.cold.3
- _xpc_endpoint_create_bs.cold.1
- _xpc_endpoint_create_bs.cold.2
- _xpc_listener_activate.cold.3
- _xpc_session_log_handle._log
- _xpc_session_log_handle._once
- os_system_version_get_current_version.cold.1
- os_system_version_get_current_version.predicate
- os_system_version_get_ios_support_version.cold.1
- os_system_version_get_ios_support_version.predicate
- os_system_version_sim_get_current_host_version.cold.1
- os_system_version_sim_get_current_host_version.predicate
CStrings:
+ "%s%s"
+ "Attempted to serialize xpc_data that is too large for what the wire protocol currently supports. Length was %zu and max supported is %u"
+ "Could not get attrs using %s for connection %s, pid %d: %d: %s"
+ "Kernel bug: Unexpected error from pipe mach_port_construct()"
+ "Kernel bug: Unexpected error from service attach port mach_port_construct()"
+ "The executable did not ship in the bundle"
+ "Tried to create an XPC data with NULL bytes and %zu length"
+ "[%p] '%s': Transaction created"
+ "[%p] '%s': Transaction released"
+ "assertion failure: \"c_block\" -> %llu"
+ "assertion failure: \"m_block\" -> %llu"
+ "assertion failure: \"prefix_len > 0\" -> %llu"
+ "audit"
+ "bssendp"
+ "bundle %s missing from disk and dyld shared cache"
+ "exception"
+ "mach port"
+ "nil"
+ "pid domain"
+ "token.pid"
- "Peer rejected"
- "Underlying connection invalidated"
- "assertion failure: \"bs_type\" -> %llu"
- "assertion failure: \"initial_state != ((void*)0)\" -> %llu"
- "assertion failure: \"label != ((void*)0)\" -> %llu"
- "assertion failure: \"name\" -> %llu"
- "bundle %s missing from disk and dyld shared cache, error=%d"
- "failed to resolve executable"
- "linked resources"
- "missing executable"

```

