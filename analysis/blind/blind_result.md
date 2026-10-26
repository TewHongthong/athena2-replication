# Blind check of the program verdict

Judged items: 120; unsure: 0; without a judgement: 0
- stratum pass (program verdict pass): human agrees on 19 of 60
- stratum fail (program verdict fail): human agrees on 43 of 60
- weighted agreement: 0.320; weighted kappa: 0.001

## Disagreements

| item | pack | kind | injected | proposed | program | human | core_failed | note |
|---|---|---|---|---|---|---|---|---|
| B002 | dotnet-runtime | method | create_serialized_string_value | CreateSerializedStringValue | pass | fail |  |  |
| B007 | godot | variable | PEER | peer | pass | fail |  |  |
| B008 | godot | method | ON_SPATIAL_CONTAINER_CLOSED | _on_spatial_container_closed | fail | pass | GODOT-METHOD-CASE |  |
| B009 | godot | method | ON_SPATIAL_CONTAINER_CLOSED | _spatial_container_closed | fail | pass | GODOT-METHOD-CASE |  |
| B010 | dotnet-runtime | method | get_system_v_amd64_pass_struct_in_register_descriptor | GetSystemV_AMD64PassStructInRegisterDescriptor | fail | pass | DOTNET-METHOD-CASE |  |
| B012 | odoo | parameter | VALS | vals | pass | fail |  |  |
| B013 | odoo | parameter | GOOGLE_SERVICE | google_service | pass | fail |  |  |
| B015 | odoo | parameter | COLLECTED_VALUES | collected_values | pass | fail |  |  |
| B017 | godot | parameter | P_SETTINGS | p_settings | pass | fail |  |  |
| B020 | dotnet-runtime | method | materialize_iid_native_type | MaterializeIidNativeType | pass | fail |  |  |
| B021 | godot | method | RESET | resetThreadState | fail | pass | GODOT-METHOD-CASE |  |
| B022 | odoo | parameter | ATTRS | attrs | pass | fail |  |  |
| B023 | godot | method | GENERATE_SAMPLE | generate_sample | pass | fail |  |  |
| B024 | dotnet-runtime | method | quantum_decimal_ieee754 | QuantumDecimalIeee754 | pass | fail |  |  |
| B027 | dotnet-runtime | method | handle_flush_target_state | flush_target_state | fail | pass | DOTNET-METHOD-CASE |  |
| B028 | godot | method | RESET_TEMP_PIVOT | reset_temporary_pivot | pass | fail |  |  |
| B034 | godot | method | GET_GROUP_COUNT | get_group_count | pass | fail |  |  |
| B035 | dotnet-runtime | method | walk | Walk | pass | fail |  |  |
| B038 | godot | method | ON_SPATIAL_CONTAINER_CLOSED | _spatial_container_closed | fail | pass | GODOT-METHOD-CASE |  |
| B039 | godot | method | GET_LENGTH | get_length | pass | fail |  |  |
| B041 | dotnet-runtime | method | divide_small_prime | DivideSmallPrime | pass | fail |  |  |
| B042 | godot | method | QUEUE_PATTERN_PREVIEW | enqueuePatternPreview | fail | pass | GODOT-METHOD-CASE |  |
| B045 | godot | method | GET_STATS | get_stats | pass | fail |  |  |
| B049 | dotnet-runtime | method | is_property_name_equivalent | IsPropertyNameEquivalent | pass | fail |  |  |
| B051 | odoo | parameter | RULE | rule | pass | fail |  |  |
| B061 | odoo | parameter | HEADERS | headers | pass | fail |  |  |
| B063 | odoo | parameter | OUT_MOVE | out_move | pass | fail |  |  |
| B064 | odoo | parameter | LOT | lot | pass | fail |  |  |
| B066 | godot | parameter | P_SHAPE | p_shape | pass | fail |  |  |
| B070 | godot | method | GENERATE_SAMPLE | generate_sample | pass | fail |  |  |
| B072 | godot | method | SET_SAMPLE_PLAYBACK | setSamplePlayback | fail | pass | GODOT-METHOD-CASE |  |
| B073 | godot | variable | PEER | peer | pass | fail |  |  |
| B074 | dotnet-runtime | method | apply_attribute | ApplyAttribute | pass | fail |  |  |
| B075 | odoo | parameter | INVOICE_LINE | invoice_line | pass | fail |  |  |
| B076 | godot | variable | CHECK | check | pass | fail |  |  |
| B079 | dotnet-runtime | method | try_get_unwind_data | TryGetUnwindData | pass | fail |  |  |
| B080 | dotnet-runtime | method | narrow_vectors_are_not_multi_slot | NarrowVectorsAreNotMultiSlot | pass | fail |  |  |
| B081 | odoo | parameter | INTERVALS | intervals | pass | fail |  |  |
| B082 | odoo | parameter | KWARGS | kwargs | pass | fail |  |  |
| B083 | godot | method | QUEUE_PATTERN_PREVIEW | queuePatternPreview | fail | pass | GODOT-METHOD-CASE |  |
| B086 | odoo | parameter | CREATE_DATE | create_date | pass | fail |  |  |
| B087 | odoo | parameter | SEQ | seq | pass | fail |  |  |
| B089 | odoo | parameter | VALS | record_vals | pass | fail |  |  |
| B090 | dotnet-runtime | method | portable_call_helpers_generator_rejects_unsupported_signature_tokens | PortableCallHelpersGenerator_RejectsUnsupportedSignatureTokens | fail | pass | DOTNET-METHOD-CASE |  |
| B093 | odoo | parameter | COLLECTED_VALUES | collected_values | pass | fail |  |  |
| B096 | dotnet-runtime | method | compute_vtable | ComputeVtable | pass | fail |  |  |
| B097 | dotnet-runtime | method | notify_on_thread_pool | NotifyOnThreadPool | pass | fail |  |  |
| B102 | dotnet-runtime | method | create_raw_owned_custom_attribute | createRawOwnedCustomAttribute | fail | pass | DOTNET-METHOD-CASE |  |
| B103 | odoo | parameter | OUT_MOVE | OutMove | fail | pass | ODOO-PARAMETER-CASE |  |
| B105 | odoo | parameter | SIZE | size | pass | fail |  |  |
| B106 | dotnet-runtime | method | enumerate_all_segments | EnumerateAllSegments | pass | fail |  |  |
| B107 | odoo | parameter | MODEL_AND_IDS | MODEL_IDS | fail | pass | ODOO-PARAMETER-CASE |  |
| B108 | dotnet-runtime | method | portable_call_helpers_generator_rejects_unsupported_signature_tokens | PortableCallHelpersGenerator_RejectsUnsupportedSignatureTokens | fail | pass | DOTNET-METHOD-CASE |  |
| B110 | dotnet-runtime | method | apply_marshal_as | ApplyMarshalAs() | fail | pass |  |  |
| B112 | dotnet-runtime | method | get_system_v_amd64_pass_struct_in_register_descriptor | GetSystemV_AMD64PassStructInRegisterDescriptor | fail | pass | DOTNET-METHOD-CASE |  |
| B114 | dotnet-runtime | method | write_async_core | _WriteAsyncCore | fail | pass | DOTNET-METHOD-CASE |  |
| B115 | odoo | parameter | TEXT | text | pass | fail |  |  |
| B116 | godot | variable | WRITE | write_amount | pass | fail |  |  |
