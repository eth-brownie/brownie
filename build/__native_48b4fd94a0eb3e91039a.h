#ifndef MYPYC_NATIVE_48b4fd94a0eb3e91039a_H
#define MYPYC_NATIVE_48b4fd94a0eb3e91039a_H
#include <Python.h>
#include <CPy.h>
#ifndef MYPYC_DECLARED_tuple_T2OF
#define MYPYC_DECLARED_tuple_T2OF
typedef struct tuple_T2OF {
    PyObject *f0;
    double f1;
} tuple_T2OF;
#endif

#ifndef MYPYC_DECLARED_tuple_T3OOO
#define MYPYC_DECLARED_tuple_T3OOO
typedef struct tuple_T3OOO {
    PyObject *f0;
    PyObject *f1;
    PyObject *f2;
} tuple_T3OOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2OI
#define MYPYC_DECLARED_tuple_T2OI
typedef struct tuple_T2OI {
    PyObject *f0;
    CPyTagged f1;
} tuple_T2OI;
#endif

#ifndef MYPYC_DECLARED_tuple_T2FO
#define MYPYC_DECLARED_tuple_T2FO
typedef struct tuple_T2FO {
    double f0;
    PyObject *f1;
} tuple_T2FO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2IO
#define MYPYC_DECLARED_tuple_T2IO
typedef struct tuple_T2IO {
    CPyTagged f0;
    PyObject *f1;
} tuple_T2IO;
#endif

#ifndef MYPYC_DECLARED_tuple_T1O
#define MYPYC_DECLARED_tuple_T1O
typedef struct tuple_T1O {
    PyObject *f0;
} tuple_T1O;
#endif

#ifndef MYPYC_DECLARED_tuple_T2OO
#define MYPYC_DECLARED_tuple_T2OO
typedef struct tuple_T2OO {
    PyObject *f0;
    PyObject *f1;
} tuple_T2OO;
#endif

#ifndef MYPYC_DECLARED_tuple_T4CIOO
#define MYPYC_DECLARED_tuple_T4CIOO
typedef struct tuple_T4CIOO {
    char f0;
    CPyTagged f1;
    PyObject *f2;
    PyObject *f3;
} tuple_T4CIOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2II
#define MYPYC_DECLARED_tuple_T2II
typedef struct tuple_T2II {
    CPyTagged f0;
    CPyTagged f1;
} tuple_T2II;
#endif

#ifndef MYPYC_DECLARED_tuple_T2IT2II
#define MYPYC_DECLARED_tuple_T2IT2II
typedef struct tuple_T2IT2II {
    CPyTagged f0;
    tuple_T2II f1;
} tuple_T2IT2II;
#endif

#ifndef MYPYC_DECLARED_tuple_T2OT2II
#define MYPYC_DECLARED_tuple_T2OT2II
typedef struct tuple_T2OT2II {
    PyObject *f0;
    tuple_T2II f1;
} tuple_T2OT2II;
#endif

#ifndef MYPYC_DECLARED_tuple_T4OOOO
#define MYPYC_DECLARED_tuple_T4OOOO
typedef struct tuple_T4OOOO {
    PyObject *f0;
    PyObject *f1;
    PyObject *f2;
    PyObject *f3;
} tuple_T4OOOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T14OOOOOOOOOOOOOO
#define MYPYC_DECLARED_tuple_T14OOOOOOOOOOOOOO
typedef struct tuple_T14OOOOOOOOOOOOOO {
    PyObject *f0;
    PyObject *f1;
    PyObject *f2;
    PyObject *f3;
    PyObject *f4;
    PyObject *f5;
    PyObject *f6;
    PyObject *f7;
    PyObject *f8;
    PyObject *f9;
    PyObject *f10;
    PyObject *f11;
    PyObject *f12;
    PyObject *f13;
} tuple_T14OOOOOOOOOOOOOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T5OOOOO
#define MYPYC_DECLARED_tuple_T5OOOOO
typedef struct tuple_T5OOOOO {
    PyObject *f0;
    PyObject *f1;
    PyObject *f2;
    PyObject *f3;
    PyObject *f4;
} tuple_T5OOOOO;
#endif

#ifndef MYPYC_DECLARED_tuple_T0
#define MYPYC_DECLARED_tuple_T0
typedef struct tuple_T0 {
    int empty_struct_error_flag;
} tuple_T0;
#endif

#ifndef MYPYC_DECLARED_tuple_T3CIO
#define MYPYC_DECLARED_tuple_T3CIO
typedef struct tuple_T3CIO {
    char f0;
    CPyTagged f1;
    PyObject *f2;
} tuple_T3CIO;
#endif

#ifndef MYPYC_DECLARED_tuple_T2CC
#define MYPYC_DECLARED_tuple_T2CC
typedef struct tuple_T2CC {
    char f0;
    char f1;
} tuple_T2CC;
#endif

#ifndef MYPYC_DECLARED_tuple_T1C
#define MYPYC_DECLARED_tuple_T1C
typedef struct tuple_T1C {
    char f0;
} tuple_T1C;
#endif

#ifndef MYPYC_DECLARED_tuple_T3IIC
#define MYPYC_DECLARED_tuple_T3IIC
typedef struct tuple_T3IIC {
    CPyTagged f0;
    CPyTagged f1;
    char f2;
} tuple_T3IIC;
#endif

#ifndef MYPYC_DECLARED_tuple_T3OOC
#define MYPYC_DECLARED_tuple_T3OOC
typedef struct tuple_T3OOC {
    PyObject *f0;
    PyObject *f1;
    char f2;
} tuple_T3OOC;
#endif

#ifndef MYPYC_DECLARED_tuple_T4CCCC
#define MYPYC_DECLARED_tuple_T4CCCC
typedef struct tuple_T4CCCC {
    char f0;
    char f1;
    char f2;
    char f3;
} tuple_T4CCCC;
#endif

#ifndef MYPYC_DECLARED_tuple_T2OC
#define MYPYC_DECLARED_tuple_T2OC
typedef struct tuple_T2OC {
    PyObject *f0;
    char f1;
} tuple_T2OC;
#endif

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_cmd;
    PyObject *_i;
    PyObject *_cmd_list;
} brownie____cli_____main_____main_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie____cli_____main_______mypyc_lambda__0_main_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_args;
    PyObject *_project_path;
    PyObject *_build_path;
    PyObject *_contract_artifact_path;
    PyObject *_interface_artifact_path;
    PyObject *_name;
    PyObject *_path;
    PyObject *_proj;
    PyObject *_codesize;
    PyObject *_contract;
    PyObject *_bytecode;
    tuple_T2OI _i;
    CPyTagged _indent;
} brownie____cli___compile___main_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie____cli___compile_____mypyc_lambda__0_main_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *_name;
} brownie____cli___console____QuitterObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *__builtins_print;
    PyObject *_console;
} brownie____cli___console___ConsolePrinterObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    char _prompt_input;
    PyObject *_exit_on_continue;
    PyObject *_compile_mode;
    PyObject *_prompt_session;
    PyObject *_console_printer;
} brownie____cli___console___ConsoleObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_locals;
} brownie____cli___console___SanitizedFileHistoryObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_console;
    PyObject *_locals;
} brownie____cli___console___ConsoleCompleterObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_console;
    PyObject *_locals;
} brownie____cli___console___ConsoleAutoSuggestObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_self;
    PyObject *_project;
    PyObject *_extra_locals;
    PyObject *_exit_on_continue;
    PyObject *_console_settings;
    PyObject *_i;
    PyObject *_locals_dict;
    PyObject *_Gui;
    PyObject *_history_file;
    PyObject *_kwargs;
    PyObject *_key_bindings;
} brownie____cli___console_____init___3_Console_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie____cli___console_____mypyc_lambda__0___3_init___3_Console_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_self;
    PyObject *_obj;
    PyObject *_k;
    PyObject *_v;
    PyObject *_results;
    PyObject *_i;
} brownie____cli___console____dir_Console_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie____cli___console_____mypyc_lambda__1__dir_Console_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_self;
    PyObject *_document;
    PyObject *_complete_event;
    PyObject *_type;
    PyObject *_value;
    PyObject *_traceback;
    PyObject *_arg;
    int32_t ___mypyc_next_label__;
    PyObject *_text;
    PyObject *_base;
    PyObject *_current;
    PyObject *_completions;
    PyObject *___mypyc_temp__0;
    PyObject *___mypyc_temp__1;
    CPyTagged ___mypyc_temp__2;
    PyObject *_i;
    PyObject *___mypyc_temp__3;
    PyObject *___mypyc_temp__4;
    CPyTagged ___mypyc_temp__5;
    PyObject *___mypyc_temp__6;
    CPyTagged ___mypyc_temp__7;
    PyObject *_key;
    tuple_T3OOO ___mypyc_temp__8;
} brownie____cli___console___get_completions_ConsoleCompleter_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_env__;
} brownie____cli___console___get_completions_ConsoleCompleter_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie____cli___console_____mypyc_lambda__2_get_completions_ConsoleCompleter_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____init___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____repr___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____getattribute___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____bool___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____contains___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____iter___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____getitem___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____len___3_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____reset_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____revert_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____add_tx_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___clear_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___copy_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___filter_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___wait_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___from_sender_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___to_receiver_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___of_address_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____gas_TxHistory_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____init___3_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____repr___3_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____len___3_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____getitem___3_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state_____iter___3_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___new_blocks_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    uint32_t bitmap;
    PyObject *_self;
    CPyTagged _height_buffer;
    CPyTagged _poll_interval;
    int32_t ___mypyc_next_label__;
    PyObject *_last_block;
    CPyTagged _last_height;
    double _last_poll;
    PyObject *_block;
} brownie___network___state___new_blocks_Chain_genObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___height_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___id_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___block_gas_limit_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___base_fee_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___priority_fee_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____revert_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____add_to_undo_buffer_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____network_connected_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state____network_disconnected_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___get_transaction_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___time_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___sleep_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___mine_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___snapshot_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___revert_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___reset_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___undo_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
} brownie___network___state___redo_Chain_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__sources;
    PyObject *__contracts;
    PyObject *__interfaces;
} brownie___project___build___BuildObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_sources;
    PyObject *_dependencies;
    PyObject *_compiler_settings;
    PyObject *_contract_name;
    PyObject *_contract_file;
    PyObject *_remappings;
    PyObject *_license;
} brownie___project___flattener___FlattenerObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_self;
    PyObject *_fp_obj;
    PyObject *_sanitize;
    PyObject *_fp;
    PyObject *_name;
    PyObject *_source;
} brownie___project___flattener___traverse_Flattener_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie___project___flattener_____mypyc_lambda__0_traverse_Flattener_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie___project___flattener_____mypyc_lambda__1_traverse_Flattener_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__path;
    PyObject *__build_path;
    PyObject *__sources;
    PyObject *__build;
    PyObject *_interface;
    PyObject *__containers;
} brownie___project___main____ProjectBaseObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__path;
    PyObject *__build_path;
    PyObject *__sources;
    PyObject *__build;
    PyObject *_interface;
    PyObject *__containers;
    PyObject *__envvars;
    PyObject *__structure;
    PyObject *__name;
    char __active;
    PyObject *__compiler_config;
    PyObject *___all__;
    PyObject *__namespaces;
} brownie___project___main___ProjectObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__path;
    PyObject *__build_path;
    PyObject *__sources;
    PyObject *__build;
    PyObject *_interface;
    PyObject *__containers;
    PyObject *__name;
} brownie___project___main___TempProjectObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *___mypyc_self__;
    PyObject *_self;
    PyObject *_chainid;
    PyObject *_path;
    PyObject *_deployments;
} brownie___project___main____load_deployments_Project_envObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___mypyc_env__;
} brownie___project___main_____mypyc_lambda__0__load_deployments_Project_objObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__contract_sources;
    PyObject *__contracts;
    PyObject *__interface_sources;
    PyObject *__interfaces;
} brownie___project___sources___SourcesObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    vectorcallfunc vectorcall;
    PyObject *___cache__;
} brownie___utils____color___ColorObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *__lock;
    PyObject *__db;
    PyObject *__cur;
    PyObject *__execute;
    PyObject *__fetchone;
    PyObject *__fetchall;
} brownie___utils___sql___CursorObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
} brownie___utils___toposort___CircularDependencyErrorObject;

typedef struct {
    PyObject_HEAD
    CPyVTableItem *vtable;
    PyObject *_data;
    int32_t ___mypyc_next_label__;
    PyObject *___mypyc_temp__0;
    CPyTagged ___mypyc_temp__1;
    CPyTagged ___mypyc_temp__2;
    PyObject *___mypyc_temp__3;
    PyObject *_k;
    PyObject *_v;
    PyObject *_extra_items_in_deps;
    PyObject *___mypyc_temp__4;
    PyObject *___mypyc_temp__5;
    PyObject *___mypyc_temp__6;
    PyObject *_item;
    PyObject *___mypyc_temp__7;
    PyObject *___mypyc_temp__8;
    CPyTagged ___mypyc_temp__9;
    CPyTagged ___mypyc_temp__10;
    PyObject *___mypyc_temp__11;
    PyObject *_dep;
    PyObject *_ordered;
    PyObject *___mypyc_temp__12;
    PyObject *___mypyc_temp__13;
    CPyTagged ___mypyc_temp__14;
    CPyTagged ___mypyc_temp__15;
    PyObject *___mypyc_temp__16;
} brownie___utils___toposort___toposort_genObject;


struct export_table_48b4fd94a0eb3e91039a {
    char (*CPyDef__cli_____top_level__)(void);
    PyTypeObject **CPyType___main_____main_env;
    PyObject *(*CPyDef___main_____main_env)(void);
    PyTypeObject **CPyType___main_______mypyc_lambda__0_main_obj;
    PyObject *(*CPyDef___main_______mypyc_lambda__0_main_obj)(void);
    PyObject *(*CPyDef___main_______mypyc_lambda__0_main_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    double (*CPyDef___main_______mypyc_lambda__0_main_obj_____call__)(PyObject *cpy_r___mypyc_self__, tuple_T2OF cpy_r_k);
    PyObject *(*CPyDef___main_____main)(void);
    char (*CPyDef___main_______top_level__)(void);
    PyObject *(*CPyDef_accounts___main)(void);
    PyObject *(*CPyDef_accounts____list)(void);
    PyObject *(*CPyDef_accounts____new)(PyObject *cpy_r_id_);
    PyObject *(*CPyDef_accounts____generate)(PyObject *cpy_r_id_);
    PyObject *(*CPyDef_accounts____import)(PyObject *cpy_r_id_, PyObject *cpy_r_path);
    PyObject *(*CPyDef_accounts____export)(PyObject *cpy_r_id_, PyObject *cpy_r_path);
    PyObject *(*CPyDef_accounts____password)(PyObject *cpy_r_id_);
    PyObject *(*CPyDef_accounts____delete)(PyObject *cpy_r_id_);
    char (*CPyDef_accounts_____top_level__)(void);
    PyObject *(*CPyDef_bake___main)(void);
    char (*CPyDef_bake_____top_level__)(void);
    PyTypeObject **CPyType_compile___main_env;
    PyObject *(*CPyDef_compile___main_env)(void);
    PyTypeObject **CPyType_compile_____mypyc_lambda__0_main_obj;
    PyObject *(*CPyDef_compile_____mypyc_lambda__0_main_obj)(void);
    PyObject *(*CPyDef_compile_____mypyc_lambda__0_main_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_compile_____mypyc_lambda__0_main_obj_____call__)(PyObject *cpy_r___mypyc_self__, tuple_T2OI cpy_r_k);
    PyObject *(*CPyDef_compile___main)(void);
    char (*CPyDef_compile_____top_level__)(void);
    PyObject **CPyStatic_console___ConsolePrinter____builtins_print;
    PyObject **CPyStatic_console___brownie____cli___console___ConsolePrinter_____call_____file;
    PyTypeObject **CPyType_console____Quitter;
    PyObject *(*CPyDef_console____Quitter)(PyObject *cpy_r_name);
    PyTypeObject **CPyType_console___ConsolePrinter;
    PyObject *(*CPyDef_console___ConsolePrinter)(PyObject *cpy_r_console);
    PyTypeObject **CPyType_console___Console;
    PyObject *(*CPyDef_console___Console)(PyObject *cpy_r_project, PyObject *cpy_r_extra_locals, PyObject *cpy_r_exit_on_continue);
    PyTypeObject **CPyType_console___SanitizedFileHistory;
    PyObject *(*CPyDef_console___SanitizedFileHistory)(PyObject *cpy_r_filename, PyObject *cpy_r_local_dict);
    PyTypeObject **CPyType_console___ConsoleCompleter;
    PyObject *(*CPyDef_console___ConsoleCompleter)(PyObject *cpy_r_console, PyObject *cpy_r_local_dict);
    PyTypeObject **CPyType_console___ConsoleAutoSuggest;
    PyObject *(*CPyDef_console___ConsoleAutoSuggest)(PyObject *cpy_r_console, PyObject *cpy_r_local_dict);
    PyTypeObject **CPyType_console_____init___3_Console_env;
    PyObject *(*CPyDef_console_____init___3_Console_env)(void);
    PyTypeObject **CPyType_console_____mypyc_lambda__0___3_init___3_Console_obj;
    PyObject *(*CPyDef_console_____mypyc_lambda__0___3_init___3_Console_obj)(void);
    PyTypeObject **CPyType_console____dir_Console_env;
    PyObject *(*CPyDef_console____dir_Console_env)(void);
    PyTypeObject **CPyType_console_____mypyc_lambda__1__dir_Console_obj;
    PyObject *(*CPyDef_console_____mypyc_lambda__1__dir_Console_obj)(void);
    PyTypeObject **CPyType_console___get_completions_ConsoleCompleter_env;
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_env)(void);
    PyTypeObject **CPyType_console___get_completions_ConsoleCompleter_gen;
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen)(void);
    PyTypeObject **CPyType_console_____mypyc_lambda__2_get_completions_ConsoleCompleter_obj;
    PyObject *(*CPyDef_console_____mypyc_lambda__2_get_completions_ConsoleCompleter_obj)(void);
    PyObject *(*CPyDef_console___main)(void);
    char (*CPyDef_console____Quitter_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_name);
    PyObject *(*CPyDef_console____Quitter_____repr__)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_console____Quitter_____call__)(PyObject *cpy_r_self, PyObject *cpy_r_code);
    char (*CPyDef_console___ConsolePrinter_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_console);
    char (*CPyDef_console___ConsolePrinter___start)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_console___ConsolePrinter_____call__)(PyObject *cpy_r_self, PyObject *cpy_r_values, PyObject *cpy_r_sep, PyObject *cpy_r_end, PyObject *cpy_r_file, PyObject *cpy_r_flush);
    char (*CPyDef_console___ConsolePrinter___finish)(PyObject *cpy_r_self);
    char (*CPyDef_console___ConsolePrinter_____mypyc_defaults_setup)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_console_____mypyc_lambda__0___3_init___3_Console_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_console_____mypyc_lambda__0___3_init___3_Console_obj_____call__)(PyObject *cpy_r___mypyc_self__);
    char (*CPyDef_console___Console_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_project, PyObject *cpy_r_extra_locals, PyObject *cpy_r_exit_on_continue);
    PyObject *(*CPyDef_console_____mypyc_lambda__1__dir_Console_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_console_____mypyc_lambda__1__dir_Console_obj_____call__)(PyObject *cpy_r___mypyc_self__, tuple_T2OO cpy_r_k);
    char (*CPyDef_console___Console____dir)(PyObject *cpy_r_self, PyObject *cpy_r_obj);
    char (*CPyDef_console___Console____console_write)(PyObject *cpy_r_self, PyObject *cpy_r_obj);
    char (*CPyDef_console___Console___interact)(PyObject *cpy_r_self, PyObject *cpy_r_args, PyObject *cpy_r_kwargs);
    PyObject *(*CPyDef_console___Console___raw_input)(PyObject *cpy_r_self, PyObject *cpy_r_prompt);
    char (*CPyDef_console___Console___showsyntaxerror)(PyObject *cpy_r_self, PyObject *cpy_r_filename);
    char (*CPyDef_console___Console___showtraceback)(PyObject *cpy_r_self);
    char (*CPyDef_console___Console___resetbuffer)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_console___Console___runsource)(PyObject *cpy_r_self, PyObject *cpy_r_source, PyObject *cpy_r_filename, PyObject *cpy_r_symbol);
    PyObject *(*CPyDef_console___Console___paste_event)(PyObject *cpy_r_self, PyObject *cpy_r_event);
    PyObject *(*CPyDef_console___Console___tab_event)(PyObject *cpy_r_self, PyObject *cpy_r_event);
    PyObject *(*CPyDef_console___Console___tab_filter)(PyObject *cpy_r_self);
    char (*CPyDef_console___Console_____mypyc_defaults_setup)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_console____dir_color)(PyObject *cpy_r_obj);
    char (*CPyDef_console___SanitizedFileHistory_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_filename, PyObject *cpy_r_local_dict);
    PyObject *(*CPyDef_console___SanitizedFileHistory___store_string)(PyObject *cpy_r_self, PyObject *cpy_r_line);
    char (*CPyDef_console___ConsoleCompleter_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_console, PyObject *cpy_r_local_dict);
    PyObject *(*CPyDef_console_____mypyc_lambda__2_get_completions_ConsoleCompleter_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_console_____mypyc_lambda__2_get_completions_ConsoleCompleter_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_k);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen_____mypyc_generator_helper__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen_____next__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen___send)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen_____iter__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen___throw)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback);
    PyObject *(*CPyDef_console___get_completions_ConsoleCompleter_gen___close)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_console___ConsoleCompleter___get_completions)(PyObject *cpy_r_self, PyObject *cpy_r_document, PyObject *cpy_r_complete_event);
    char (*CPyDef_console___ConsoleAutoSuggest_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_console, PyObject *cpy_r_local_dict);
    PyObject *(*CPyDef_console___ConsoleAutoSuggest___get_suggestion)(PyObject *cpy_r_self, PyObject *cpy_r_buffer, PyObject *cpy_r_document);
    PyObject *(*CPyDef_console____obj_from_token)(PyObject *cpy_r_obj, PyObject *cpy_r_token);
    PyObject *(*CPyDef_console____parse_document)(PyObject *cpy_r_local_dict, PyObject *cpy_r_text);
    char (*CPyDef_console_____top_level__)(void);
    PyObject *(*CPyDef_gui___main)(void);
    char (*CPyDef_gui_____top_level__)(void);
    PyObject *(*CPyDef_init___main)(void);
    char (*CPyDef_init_____top_level__)(void);
    PyObject *(*CPyDef_networks___main)(void);
    PyObject *(*CPyDef_networks____list)(PyObject *cpy_r_verbose);
    PyObject *(*CPyDef_networks____add)(PyObject *cpy_r_env, PyObject *cpy_r_id_, PyObject *cpy_r_args);
    PyObject *(*CPyDef_networks____modify)(PyObject *cpy_r_id_, PyObject *cpy_r_args);
    PyObject *(*CPyDef_networks____delete)(PyObject *cpy_r_id_);
    PyObject *(*CPyDef_networks____import)(PyObject *cpy_r_path_str, PyObject *cpy_r_replace);
    PyObject *(*CPyDef_networks____export)(PyObject *cpy_r_path_str);
    PyObject *(*CPyDef_networks____update_provider)(PyObject *cpy_r_name, PyObject *cpy_r_url);
    PyObject *(*CPyDef_networks____delete_provider)(PyObject *cpy_r_name);
    PyObject *(*CPyDef_networks____set_provider)(PyObject *cpy_r_name);
    PyObject *(*CPyDef_networks____list_providers)(PyObject *cpy_r_verbose);
    PyObject *(*CPyDef_networks____parse_args)(PyObject *cpy_r_args);
    char (*CPyDef_networks____print_verbose_providers_description)(PyObject *cpy_r_providers);
    char (*CPyDef_networks____print_simple_providers_description)(PyObject *cpy_r_providers);
    char (*CPyDef_networks____print_simple_network_description)(PyObject *cpy_r_network_dict, PyObject *cpy_r_is_last);
    char (*CPyDef_networks____print_verbose_network_description)(PyObject *cpy_r_network_dict, PyObject *cpy_r_is_last, PyObject *cpy_r_indent);
    char (*CPyDef_networks____validate_network)(PyObject *cpy_r_network, PyObject *cpy_r_required);
    char (*CPyDef_networks_____top_level__)(void);
    PyObject *(*CPyDef_pm___main)(void);
    PyObject *(*CPyDef_pm____list)(void);
    PyObject *(*CPyDef_pm____clone)(PyObject *cpy_r_package_id, PyObject *cpy_r_path_str);
    PyObject *(*CPyDef_pm____delete)(PyObject *cpy_r_package_id);
    PyObject *(*CPyDef_pm____install)(PyObject *cpy_r_uri);
    PyObject *(*CPyDef_pm____split_id)(PyObject *cpy_r_package_id);
    PyObject *(*CPyDef_pm____format_pkg)(PyObject *cpy_r_org, PyObject *cpy_r_repo, PyObject *cpy_r_version);
    char (*CPyDef_pm_____top_level__)(void);
    PyObject *(*CPyDef_run___main)(void);
    char (*CPyDef_run_____top_level__)(void);
    PyObject *(*CPyDef_test___main)(void);
    char (*CPyDef_test_____top_level__)(void);
    char (*CPyDef_convert_____top_level__)(void);
    PyObject **CPyStatic_convert___main___HexBytes;
    PyObject **CPyStatic_convert___main___is_hex;
    PyObject **CPyStatic_convert___main___to_text;
    PyObject **CPyStatic_convert___main____TEN_DECIMALS;
    PyObject *(*CPyDef_convert___main___to_uint)(PyObject *cpy_r_value, PyObject *cpy_r_type_str);
    PyObject *(*CPyDef_convert___main___to_int)(PyObject *cpy_r_value, PyObject *cpy_r_type_str);
    PyObject *(*CPyDef_convert___main___to_decimal)(PyObject *cpy_r_value);
    PyObject *(*CPyDef_convert___main___to_address)(PyObject *cpy_r_value);
    PyObject *(*CPyDef_convert___main___to_bytes)(PyObject *cpy_r_value, PyObject *cpy_r_type_str);
    char (*CPyDef_convert___main___to_bool)(PyObject *cpy_r_value);
    PyObject *(*CPyDef_convert___main___to_string)(PyObject *cpy_r_value);
    char (*CPyDef_convert___main_____top_level__)(void);
    PyObject **CPyStatic_normalize____TupleType;
    PyObject **CPyStatic_normalize____parse;
    PyObject *(*CPyDef_normalize___format_input)(PyObject *cpy_r_abi, PyObject *cpy_r_inputs);
    PyObject *(*CPyDef_normalize___format_output)(PyObject *cpy_r_abi, PyObject *cpy_r_outputs);
    PyObject *(*CPyDef_normalize___format_event)(PyObject *cpy_r_event);
    PyObject *(*CPyDef_normalize____format_tuple)(PyObject *cpy_r_abi_types, PyObject *cpy_r_values);
    PyObject *(*CPyDef_normalize____format_array)(PyObject *cpy_r_abi_type, PyObject *cpy_r_values);
    PyObject *(*CPyDef_normalize____format_single)(PyObject *cpy_r_type_str, PyObject *cpy_r_value);
    char (*CPyDef_normalize____check_array)(PyObject *cpy_r_values, PyObject *cpy_r_length);
    PyObject *(*CPyDef_normalize____get_abi_types)(PyObject *cpy_r_abi_params);
    char (*CPyDef_normalize_____top_level__)(void);
    PyObject **CPyStatic_convert___utils___keccak;
    PyObject **CPyStatic_convert___utils____cached_int_bounds;
    tuple_T2II (*CPyDef_convert___utils___get_int_bounds)(PyObject *cpy_r_type_str);
    PyObject *(*CPyDef_convert___utils___get_type_strings)(PyObject *cpy_r_abi_params, PyObject *cpy_r_substitutions);
    PyObject *(*CPyDef_convert___utils___build_function_signature)(PyObject *cpy_r_abi);
    PyObject *(*CPyDef_convert___utils___build_function_selector)(PyObject *cpy_r_abi);
    char (*CPyDef_convert___utils_____top_level__)(void);
    PyObject **CPyStatic_network___accounts;
    PyObject **CPyStatic_network___rpc;
    PyObject **CPyStatic_network___history;
    PyObject **CPyStatic_network___chain;
    char (*CPyDef_network_____top_level__)(void);
    PyObject **CPyStatic_state___cur;
    PyTypeObject **CPyType_state___TxHistory;
    PyTypeObject **CPyType_state___Chain;
    PyTypeObject **CPyType_state_____init___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____init___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____repr___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____repr___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____getattribute___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____getattribute___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____bool___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____bool___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____contains___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____contains___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____iter___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____iter___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____getitem___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____getitem___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____len___3_TxHistory_obj;
    PyObject *(*CPyDef_state_____len___3_TxHistory_obj)(void);
    PyTypeObject **CPyType_state____reset_TxHistory_obj;
    PyObject *(*CPyDef_state____reset_TxHistory_obj)(void);
    PyTypeObject **CPyType_state____revert_TxHistory_obj;
    PyObject *(*CPyDef_state____revert_TxHistory_obj)(void);
    PyTypeObject **CPyType_state____add_tx_TxHistory_obj;
    PyObject *(*CPyDef_state____add_tx_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___clear_TxHistory_obj;
    PyObject *(*CPyDef_state___clear_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___copy_TxHistory_obj;
    PyObject *(*CPyDef_state___copy_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___filter_TxHistory_obj;
    PyObject *(*CPyDef_state___filter_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___wait_TxHistory_obj;
    PyObject *(*CPyDef_state___wait_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___from_sender_TxHistory_obj;
    PyObject *(*CPyDef_state___from_sender_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___to_receiver_TxHistory_obj;
    PyObject *(*CPyDef_state___to_receiver_TxHistory_obj)(void);
    PyTypeObject **CPyType_state___of_address_TxHistory_obj;
    PyObject *(*CPyDef_state___of_address_TxHistory_obj)(void);
    PyTypeObject **CPyType_state____gas_TxHistory_obj;
    PyObject *(*CPyDef_state____gas_TxHistory_obj)(void);
    PyTypeObject **CPyType_state_____init___3_Chain_obj;
    PyObject *(*CPyDef_state_____init___3_Chain_obj)(void);
    PyTypeObject **CPyType_state_____repr___3_Chain_obj;
    PyObject *(*CPyDef_state_____repr___3_Chain_obj)(void);
    PyTypeObject **CPyType_state_____len___3_Chain_obj;
    PyObject *(*CPyDef_state_____len___3_Chain_obj)(void);
    PyTypeObject **CPyType_state_____getitem___3_Chain_obj;
    PyObject *(*CPyDef_state_____getitem___3_Chain_obj)(void);
    PyTypeObject **CPyType_state_____iter___3_Chain_obj;
    PyObject *(*CPyDef_state_____iter___3_Chain_obj)(void);
    PyTypeObject **CPyType_state___new_blocks_Chain_obj;
    PyObject *(*CPyDef_state___new_blocks_Chain_obj)(void);
    PyTypeObject **CPyType_state___new_blocks_Chain_gen;
    PyObject *(*CPyDef_state___new_blocks_Chain_gen)(void);
    PyTypeObject **CPyType_state___height_Chain_obj;
    PyObject *(*CPyDef_state___height_Chain_obj)(void);
    PyTypeObject **CPyType_state___id_Chain_obj;
    PyObject *(*CPyDef_state___id_Chain_obj)(void);
    PyTypeObject **CPyType_state___block_gas_limit_Chain_obj;
    PyObject *(*CPyDef_state___block_gas_limit_Chain_obj)(void);
    PyTypeObject **CPyType_state___base_fee_Chain_obj;
    PyObject *(*CPyDef_state___base_fee_Chain_obj)(void);
    PyTypeObject **CPyType_state___priority_fee_Chain_obj;
    PyObject *(*CPyDef_state___priority_fee_Chain_obj)(void);
    PyTypeObject **CPyType_state____revert_Chain_obj;
    PyObject *(*CPyDef_state____revert_Chain_obj)(void);
    PyTypeObject **CPyType_state____add_to_undo_buffer_Chain_obj;
    PyObject *(*CPyDef_state____add_to_undo_buffer_Chain_obj)(void);
    PyTypeObject **CPyType_state____network_connected_Chain_obj;
    PyObject *(*CPyDef_state____network_connected_Chain_obj)(void);
    PyTypeObject **CPyType_state____network_disconnected_Chain_obj;
    PyObject *(*CPyDef_state____network_disconnected_Chain_obj)(void);
    PyTypeObject **CPyType_state___get_transaction_Chain_obj;
    PyObject *(*CPyDef_state___get_transaction_Chain_obj)(void);
    PyTypeObject **CPyType_state___time_Chain_obj;
    PyObject *(*CPyDef_state___time_Chain_obj)(void);
    PyTypeObject **CPyType_state___sleep_Chain_obj;
    PyObject *(*CPyDef_state___sleep_Chain_obj)(void);
    PyTypeObject **CPyType_state___mine_Chain_obj;
    PyObject *(*CPyDef_state___mine_Chain_obj)(void);
    PyTypeObject **CPyType_state___snapshot_Chain_obj;
    PyObject *(*CPyDef_state___snapshot_Chain_obj)(void);
    PyTypeObject **CPyType_state___revert_Chain_obj;
    PyObject *(*CPyDef_state___revert_Chain_obj)(void);
    PyTypeObject **CPyType_state___reset_Chain_obj;
    PyObject *(*CPyDef_state___reset_Chain_obj)(void);
    PyTypeObject **CPyType_state___undo_Chain_obj;
    PyObject *(*CPyDef_state___undo_Chain_obj)(void);
    PyTypeObject **CPyType_state___redo_Chain_obj;
    PyObject *(*CPyDef_state___redo_Chain_obj)(void);
    PyObject *(*CPyDef_state_____init___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state_____init___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____repr___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____repr___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____getattribute___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____getattribute___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_name);
    PyObject *(*CPyDef_state_____bool___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state_____bool___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____contains___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state_____contains___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_item);
    PyObject *(*CPyDef_state_____iter___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____iter___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____getitem___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____getitem___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_key);
    PyObject *(*CPyDef_state_____len___3_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_state_____len___3_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state____reset_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____reset_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state____revert_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____revert_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_height);
    PyObject *(*CPyDef_state____add_tx_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____add_tx_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_tx);
    PyObject *(*CPyDef_state___clear_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state___clear_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, char cpy_r_only_confirmed);
    PyObject *(*CPyDef_state___copy_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___copy_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___filter_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___filter_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_key, PyObject *cpy_r_kwargs);
    PyObject *(*CPyDef_state___wait_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state___wait_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_key, PyObject *cpy_r_kwargs);
    PyObject *(*CPyDef_state___from_sender_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___from_sender_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_account);
    PyObject *(*CPyDef_state___to_receiver_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___to_receiver_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_account);
    PyObject *(*CPyDef_state___of_address_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___of_address_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_account);
    PyObject *(*CPyDef_state____gas_TxHistory_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____gas_TxHistory_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_fn_name, CPyTagged cpy_r_gas_used, char cpy_r_is_success);
    PyObject *(*CPyDef_state_____init___3_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state_____init___3_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____repr___3_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____repr___3_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____len___3_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_state_____len___3_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state_____getitem___3_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____getitem___3_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_block_number);
    PyObject *(*CPyDef_state_____iter___3_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state_____iter___3_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___new_blocks_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen_____mypyc_generator_helper__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen_____next__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen___send)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen_____iter__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen___throw)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback);
    PyObject *(*CPyDef_state___new_blocks_Chain_gen___close)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_state___new_blocks_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_height_buffer, CPyTagged cpy_r_poll_interval);
    PyObject *(*CPyDef_state___height_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___height_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___id_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_state___id_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___block_gas_limit_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___block_gas_limit_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___base_fee_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___base_fee_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___priority_fee_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___priority_fee_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state____revert_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_state____revert_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_id_);
    PyObject *(*CPyDef_state____add_to_undo_buffer_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____add_to_undo_buffer_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_tx, PyObject *cpy_r_fn, PyObject *cpy_r_args, PyObject *cpy_r_kwargs);
    PyObject *(*CPyDef_state____network_connected_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____network_connected_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state____network_disconnected_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state____network_disconnected_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___get_transaction_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___get_transaction_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, PyObject *cpy_r_txid);
    PyObject *(*CPyDef_state___time_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    CPyTagged (*CPyDef_state___time_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___sleep_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state___sleep_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_seconds);
    PyObject *(*CPyDef_state___mine_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___mine_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_blocks, PyObject *cpy_r_timestamp, PyObject *cpy_r_timedelta);
    PyObject *(*CPyDef_state___snapshot_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    char (*CPyDef_state___snapshot_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___revert_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___revert_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___reset_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___reset_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self);
    PyObject *(*CPyDef_state___undo_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___undo_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_num);
    PyObject *(*CPyDef_state___redo_Chain_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_state___redo_Chain_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_self, CPyTagged cpy_r_num);
    char (*CPyDef_state____revert_register)(PyObject *cpy_r_obj);
    char (*CPyDef_state____notify_registry)(PyObject *cpy_r_height);
    PyObject *(*CPyDef_state____find_contract)(PyObject *cpy_r_address);
    PyObject *(*CPyDef_state____get_current_dependencies)(void);
    char (*CPyDef_state____add_contract)(PyObject *cpy_r_contract);
    char (*CPyDef_state____remove_contract)(PyObject *cpy_r_contract);
    tuple_T2OO (*CPyDef_state____get_deployment)(PyObject *cpy_r_address, PyObject *cpy_r_alias);
    char (*CPyDef_state____add_deployment)(PyObject *cpy_r_contract, PyObject *cpy_r_alias);
    tuple_T2OO (*CPyDef_state____remove_deployment)(PyObject *cpy_r_address, PyObject *cpy_r_alias);
    char (*CPyDef_state_____top_level__)(void);
    char (*CPyDef_project_____top_level__)(void);
    PyObject **CPyStatic_compiler___Path;
    PyObject **CPyStatic_compiler___deepcopy;
    PyObject **CPyStatic_compiler___sha1;
    PyObject **CPyStatic_compiler___Version;
    PyObject **CPyStatic_compiler____from_standard_output;
    PyObject *(*CPyDef_compiler___compile_and_format)(PyObject *cpy_r_contract_sources, PyObject *cpy_r_solc_version, PyObject *cpy_r_vyper_version, PyObject *cpy_r_optimize, PyObject *cpy_r_runs, PyObject *cpy_r_evm_version, char cpy_r_silent, PyObject *cpy_r_allow_paths, PyObject *cpy_r_interface_sources, PyObject *cpy_r_remappings, PyObject *cpy_r_optimizer, PyObject *cpy_r_viaIR);
    PyObject *(*CPyDef_compiler___generate_input_json)(PyObject *cpy_r_contract_sources, char cpy_r_optimize, CPyTagged cpy_r_runs, PyObject *cpy_r_evm_version, PyObject *cpy_r_language, PyObject *cpy_r_interface_sources, PyObject *cpy_r_remappings, PyObject *cpy_r_optimizer, PyObject *cpy_r_viaIR);
    PyObject *(*CPyDef_compiler____get_solc_remappings)(PyObject *cpy_r_remappings);
    PyObject *(*CPyDef_compiler____get_allow_paths)(PyObject *cpy_r_allow_paths, PyObject *cpy_r_remappings);
    PyObject *(*CPyDef_compiler___compile_from_input_json)(PyObject *cpy_r_input_json, char cpy_r_silent, PyObject *cpy_r_allow_paths);
    PyObject *(*CPyDef_compiler___generate_build_json)(PyObject *cpy_r_input_json, PyObject *cpy_r_output_json, PyObject *cpy_r_compiler_data, char cpy_r_silent);
    PyObject *(*CPyDef_compiler____sources_dict)(PyObject *cpy_r_original, PyObject *cpy_r_language);
    PyObject *(*CPyDef_compiler___get_abi)(PyObject *cpy_r_contract_sources, PyObject *cpy_r_solc_version, PyObject *cpy_r_allow_paths, PyObject *cpy_r_remappings, char cpy_r_silent);
    char (*CPyDef_compiler_____top_level__)(void);
    PyObject **CPyStatic_solidity___solcx_logger;
    PyObject **CPyStatic_solidity___sh;
    PyObject **CPyStatic_solidity___EVM_VERSION_MAPPING;
    PyObject **CPyStatic_solidity____BINOPS_PARAMS;
    PyObject *(*CPyDef_solidity___get_version)(void);
    PyObject *(*CPyDef_solidity___compile_from_input_json)(PyObject *cpy_r_input_json, char cpy_r_silent, PyObject *cpy_r_allow_paths);
    PyObject *(*CPyDef_solidity___set_solc_version)(PyObject *cpy_r_version);
    char (*CPyDef_solidity___install_solc)(PyObject *cpy_r_versions);
    PyObject *(*CPyDef_solidity___get_abi)(PyObject *cpy_r_contract_source, PyObject *cpy_r_allow_paths);
    PyObject *(*CPyDef_solidity___find_solc_versions)(PyObject *cpy_r_contract_sources, char cpy_r_install_needed, char cpy_r_install_latest, char cpy_r_silent);
    PyObject *(*CPyDef_solidity___find_best_solc_version)(PyObject *cpy_r_contract_sources, char cpy_r_install_needed, char cpy_r_install_latest, char cpy_r_silent);
    tuple_T2OO (*CPyDef_solidity____get_solc_version_list)(void);
    PyObject *(*CPyDef_solidity____get_unique_build_json)(PyObject *cpy_r_output_evm, PyObject *cpy_r_contract_node, PyObject *cpy_r_stmt_nodes, PyObject *cpy_r_branch_nodes, char cpy_r_has_fallback);
    PyObject *(*CPyDef_solidity____format_link_references)(PyObject *cpy_r_evm);
    PyObject *(*CPyDef_solidity____remove_metadata)(PyObject *cpy_r_bytecode);
    tuple_T3OOO (*CPyDef_solidity____generate_coverage_data)(PyObject *cpy_r_source_map_str, PyObject *cpy_r_opcodes_str, PyObject *cpy_r_contract_node, PyObject *cpy_r_stmt_nodes, PyObject *cpy_r_branch_nodes, char cpy_r_has_fallback, CPyTagged cpy_r_instruction_count);
    char (*CPyDef_solidity____find_revert_offset)(PyObject *cpy_r_pc_list, PyObject *cpy_r_source_map, PyObject *cpy_r_source_node, PyObject *cpy_r_fn_node, PyObject *cpy_r_fn_name);
    char (*CPyDef_solidity____set_invalid_error_string)(PyObject *cpy_r_source_node, PyObject *cpy_r_pc_map);
    tuple_T2OO (*CPyDef_solidity____get_active_fn)(PyObject *cpy_r_source_node, tuple_T2II cpy_r_offset);
    tuple_T3OOO (*CPyDef_solidity____get_nodes)(PyObject *cpy_r_output_json);
    PyObject *(*CPyDef_solidity____get_statement_nodes)(PyObject *cpy_r_source_nodes);
    PyObject *(*CPyDef_solidity____get_branch_nodes)(PyObject *cpy_r_source_nodes);
    PyObject *(*CPyDef_solidity____get_recursive_branches)(PyObject *cpy_r_base_node);
    char (*CPyDef_solidity____is_rightmost_operation)(PyObject *cpy_r_node, CPyTagged cpy_r_depth);
    char (*CPyDef_solidity____check_left_operator)(PyObject *cpy_r_node, CPyTagged cpy_r_depth);
    char (*CPyDef_solidity_____top_level__)(void);
    PyObject **CPyStatic_compiler___utils___Path;
    PyObject *(*CPyDef_compiler___utils___expand_source_map)(PyObject *cpy_r_source_map_str);
    PyObject *(*CPyDef_compiler___utils____expand_row)(PyObject *cpy_r_row);
    PyObject *(*CPyDef_compiler___utils___merge_natspec)(PyObject *cpy_r_devdoc, PyObject *cpy_r_userdoc);
    PyObject *(*CPyDef_compiler___utils____get_alias)(PyObject *cpy_r_contract_name, PyObject *cpy_r_path_str);
    char (*CPyDef_compiler___utils_____top_level__)(void);
    PyObject **CPyStatic_vyper___vvm_logger;
    PyObject **CPyStatic_vyper___sh;
    PyObject **CPyStatic_vyper___EVM_VERSION_MAPPING;
    PyObject *(*CPyDef_vyper___get_version)(void);
    PyObject *(*CPyDef_vyper___set_vyper_version)(PyObject *cpy_r_version);
    PyObject *(*CPyDef_vyper___get_abi)(PyObject *cpy_r_contract_source, PyObject *cpy_r_name);
    tuple_T2OO (*CPyDef_vyper____get_vyper_version_list)(void);
    char (*CPyDef_vyper___install_vyper)(PyObject *cpy_r_versions);
    PyObject *(*CPyDef_vyper___find_vyper_versions)(PyObject *cpy_r_contract_sources, char cpy_r_install_needed, char cpy_r_install_latest, char cpy_r_silent);
    PyObject *(*CPyDef_vyper___find_best_vyper_version)(PyObject *cpy_r_contract_sources, char cpy_r_install_needed, char cpy_r_install_latest, char cpy_r_silent);
    PyObject *(*CPyDef_vyper___compile_from_input_json)(PyObject *cpy_r_input_json, char cpy_r_silent, PyObject *cpy_r_allow_paths);
    PyObject *(*CPyDef_vyper____get_unique_build_json)(PyObject *cpy_r_output_evm, PyObject *cpy_r_path_str, PyObject *cpy_r_contract_name, PyObject *cpy_r_ast_json, PyObject *cpy_r_offset);
    PyObject *(*CPyDef_vyper____get_dependencies)(PyObject *cpy_r_ast_json);
    char (*CPyDef_vyper____is_revert_jump)(PyObject *cpy_r_pc_list, CPyTagged cpy_r_revert_pc);
    tuple_T3OOO (*CPyDef_vyper____generate_coverage_data)(PyObject *cpy_r_source_map_str, PyObject *cpy_r_opcodes_str, PyObject *cpy_r_contract_name, PyObject *cpy_r_ast_json);
    tuple_T2II (*CPyDef_vyper____convert_src)(PyObject *cpy_r_src);
    PyObject *(*CPyDef_vyper____find_node_by_offset)(PyObject *cpy_r_ast_json, tuple_T2II cpy_r_offset);
    PyObject *(*CPyDef_vyper____get_statement_nodes)(PyObject *cpy_r_ast_json);
    PyObject *(*CPyDef_vyper____convert_to_semver)(PyObject *cpy_r_versions);
    char (*CPyDef_vyper_____top_level__)(void);
    PyTypeObject **CPyType_build___Build;
    PyObject *(*CPyDef_build___Build)(PyObject *cpy_r_sources);
    char (*CPyDef_build___Build_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_sources);
    char (*CPyDef_build___Build____add_contract)(PyObject *cpy_r_self, PyObject *cpy_r_build_json, PyObject *cpy_r_alias);
    char (*CPyDef_build___Build____add_interface)(PyObject *cpy_r_self, PyObject *cpy_r_build_json);
    char (*CPyDef_build___Build____generate_revert_map)(PyObject *cpy_r_self, PyObject *cpy_r_pcMap, PyObject *cpy_r_source_map, PyObject *cpy_r_language);
    char (*CPyDef_build___Build____remove_contract)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    char (*CPyDef_build___Build____remove_interface)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    PyObject *(*CPyDef_build___Build___get)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    PyObject *(*CPyDef_build___Build___items)(PyObject *cpy_r_self, PyObject *cpy_r_path);
    char (*CPyDef_build___Build___contains)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    PyObject *(*CPyDef_build___Build___get_dependents)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    PyObject *(*CPyDef_build___Build____stem)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    PyObject *(*CPyDef_build____get_dev_revert)(CPyTagged cpy_r_pc);
    PyObject *(*CPyDef_build____get_error_source_from_pc)(CPyTagged cpy_r_pc, CPyTagged cpy_r_pad);
    char (*CPyDef_build_____top_level__)(void);
    PyObject **CPyStatic_flattener___IMPORT_PATTERN;
    PyObject **CPyStatic_flattener___PRAGMA_PATTERN;
    PyObject **CPyStatic_flattener___LICENSE_PATTERN;
    PyObject **CPyStatic_flattener____Path;
    PyObject **CPyStatic_flattener____defaultdict;
    PyObject **CPyStatic_flattener____sub;
    PyObject **CPyStatic_flattener____mapcat;
    PyObject **CPyStatic_flattener____IMPORT_PATTERN_FINDITER;
    PyObject **CPyStatic_flattener____IMPORT_PATTERN_SUB;
    PyObject **CPyStatic_flattener____PRAGMA_PATTERN_FINDALL;
    PyObject **CPyStatic_flattener____PRAGMA_PATTERN_SUB;
    PyObject **CPyStatic_flattener____LICENSE_PATTERN_SEARCH;
    PyObject **CPyStatic_flattener____LICENSE_PATTERN_SUB;
    PyTypeObject **CPyType_flattener___Flattener;
    PyObject *(*CPyDef_flattener___Flattener)(PyObject *cpy_r_primary_source_fp, PyObject *cpy_r_contract_name, PyObject *cpy_r_remappings, PyObject *cpy_r_compiler_settings);
    PyTypeObject **CPyType_flattener___traverse_Flattener_env;
    PyObject *(*CPyDef_flattener___traverse_Flattener_env)(void);
    PyTypeObject **CPyType_flattener_____mypyc_lambda__0_traverse_Flattener_obj;
    PyObject *(*CPyDef_flattener_____mypyc_lambda__0_traverse_Flattener_obj)(void);
    PyTypeObject **CPyType_flattener_____mypyc_lambda__1_traverse_Flattener_obj;
    PyObject *(*CPyDef_flattener_____mypyc_lambda__1_traverse_Flattener_obj)(void);
    char (*CPyDef_flattener___Flattener_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_primary_source_fp, PyObject *cpy_r_contract_name, PyObject *cpy_r_remappings, PyObject *cpy_r_compiler_settings);
    PyObject *(*CPyDef_flattener___Flattener___path_to_name)(PyObject *cpy_r_cls, PyObject *cpy_r_pth);
    PyObject *(*CPyDef_flattener_____mypyc_lambda__0_traverse_Flattener_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_flattener_____mypyc_lambda__0_traverse_Flattener_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_path);
    PyObject *(*CPyDef_flattener_____mypyc_lambda__1_traverse_Flattener_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_flattener_____mypyc_lambda__1_traverse_Flattener_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_m);
    char (*CPyDef_flattener___Flattener___traverse)(PyObject *cpy_r_self, PyObject *cpy_r_fp);
    PyObject *(*CPyDef_flattener___Flattener___flattened_source)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_flattener___Flattener___standard_input_json)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_flattener___Flattener___remap_import)(PyObject *cpy_r_self, PyObject *cpy_r_import_path);
    PyObject *(*CPyDef_flattener___Flattener___make_import_absolute)(PyObject *cpy_r_import_path, PyObject *cpy_r_source_file_dir);
    PyObject *(*CPyDef_flattener____wipe)(PyObject *cpy_r_src);
    char (*CPyDef_flattener_____top_level__)(void);
    PyObject **CPyStatic_project___main___BUILD_FOLDERS;
    PyObject **CPyStatic_project___main____loaded_projects;
    PyObject **CPyStatic_project___main___brownie___project___main____stream_download___headers;
    PyObject **CPyStatic_project___main___brownie___project___main____get_mix_default_branch___headers;
    PyTypeObject **CPyType_project___main____ProjectBase;
    PyObject *(*CPyDef_project___main____ProjectBase)(void);
    PyTypeObject **CPyType_project___main___Project;
    PyObject *(*CPyDef_project___main___Project)(PyObject *cpy_r_name, PyObject *cpy_r_project_path, char cpy_r_compile);
    PyTypeObject **CPyType_project___main___TempProject;
    PyObject *(*CPyDef_project___main___TempProject)(PyObject *cpy_r_name, PyObject *cpy_r_contract_sources, PyObject *cpy_r_compiler_config);
    PyTypeObject **CPyType_project___main____load_deployments_Project_env;
    PyObject *(*CPyDef_project___main____load_deployments_Project_env)(void);
    PyTypeObject **CPyType_project___main_____mypyc_lambda__0__load_deployments_Project_obj;
    PyObject *(*CPyDef_project___main_____mypyc_lambda__0__load_deployments_Project_obj)(void);
    char (*CPyDef_project___main____ProjectBase____compile)(PyObject *cpy_r_self, PyObject *cpy_r_contract_sources, PyObject *cpy_r_compiler_config, char cpy_r_silent);
    char (*CPyDef_project___main____ProjectBase____create_containers)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main____ProjectBase_____getitem__)(PyObject *cpy_r_self, PyObject *cpy_r_key);
    PyObject *(*CPyDef_project___main____ProjectBase_____iter__)(PyObject *cpy_r_self);
    CPyTagged (*CPyDef_project___main____ProjectBase_____len__)(PyObject *cpy_r_self);
    char (*CPyDef_project___main____ProjectBase_____contains__)(PyObject *cpy_r_self, PyObject *cpy_r_item);
    PyObject *(*CPyDef_project___main____ProjectBase___dict)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main____ProjectBase___keys)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___Project_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_name, PyObject *cpy_r_project_path, char cpy_r_compile);
    char (*CPyDef_project___main___Project___load)(PyObject *cpy_r_self, char cpy_r_raise_if_loaded, char cpy_r_compile);
    PyObject *(*CPyDef_project___main___Project____get_changed_contracts)(PyObject *cpy_r_self, PyObject *cpy_r_compiled_hashes);
    char (*CPyDef_project___main___Project____compare_build_json)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name);
    char (*CPyDef_project___main___Project____compile_interfaces)(PyObject *cpy_r_self, PyObject *cpy_r_compiled_hashes);
    char (*CPyDef_project___main___Project____load_dependency_artifacts)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main_____mypyc_lambda__0__load_deployments_Project_obj_____get__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_instance, PyObject *cpy_r_owner);
    PyObject *(*CPyDef_project___main_____mypyc_lambda__0__load_deployments_Project_obj_____call__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_k);
    char (*CPyDef_project___main___Project____load_deployments)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main___Project____load_deployment_map)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___Project____save_deployment_map)(PyObject *cpy_r_self, PyObject *cpy_r_deployment_map);
    char (*CPyDef_project___main___Project____remove_from_deployment_map)(PyObject *cpy_r_self, PyObject *cpy_r_contract);
    char (*CPyDef_project___main___Project____add_to_deployment_map)(PyObject *cpy_r_self, PyObject *cpy_r_contract);
    char (*CPyDef_project___main___Project____update_and_register)(PyObject *cpy_r_self, PyObject *cpy_r_dict_);
    char (*CPyDef_project___main___Project____add_to_main_namespace)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___Project____remove_from_main_namespace)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main___Project_____repr__)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___Project___load_config)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___Project___close)(PyObject *cpy_r_self, char cpy_r_raises);
    char (*CPyDef_project___main___Project____clear_dev_deployments)(PyObject *cpy_r_self, CPyTagged cpy_r_height);
    char (*CPyDef_project___main___Project____revert)(PyObject *cpy_r_self, CPyTagged cpy_r_height);
    char (*CPyDef_project___main___Project____reset)(PyObject *cpy_r_self);
    char (*CPyDef_project___main___TempProject_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_name, PyObject *cpy_r_contract_sources, PyObject *cpy_r_compiler_config);
    PyObject *(*CPyDef_project___main___TempProject_____repr__)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_project___main___check_for_project)(PyObject *cpy_r_path);
    PyObject *(*CPyDef_project___main___get_loaded_projects)(void);
    PyObject *(*CPyDef_project___main___new)(PyObject *cpy_r_project_path_str, char cpy_r_ignore_subfolder, char cpy_r_ignore_existing);
    PyObject *(*CPyDef_project___main___from_brownie_mix)(PyObject *cpy_r_project_name, PyObject *cpy_r_project_path, char cpy_r_ignore_subfolder);
    PyObject *(*CPyDef_project___main___compile_source)(PyObject *cpy_r_source, PyObject *cpy_r_solc_version, PyObject *cpy_r_vyper_version, char cpy_r_optimize, PyObject *cpy_r_runs, PyObject *cpy_r_evm_version);
    PyObject *(*CPyDef_project___main___load)(PyObject *cpy_r_project_path, PyObject *cpy_r_name, char cpy_r_raise_if_loaded, char cpy_r_compile);
    char (*CPyDef_project___main____install_dependencies)(PyObject *cpy_r_path);
    PyObject *(*CPyDef_project___main___install_package)(PyObject *cpy_r_package_id);
    PyObject *(*CPyDef_project___main____maybe_retrieve_github_auth)(void);
    PyObject *(*CPyDef_project___main____install_from_github)(PyObject *cpy_r_package_id);
    PyObject *(*CPyDef_project___main____get_download_url_from_tag)(PyObject *cpy_r_org, PyObject *cpy_r_repo, PyObject *cpy_r_version, PyObject *cpy_r_headers);
    char (*CPyDef_project___main____create_gitfiles)(PyObject *cpy_r_project_path);
    char (*CPyDef_project___main____create_folders)(PyObject *cpy_r_project_path);
    char (*CPyDef_project___main____add_to_sys_path)(PyObject *cpy_r_project_path);
    char (*CPyDef_project___main____compare_settings)(PyObject *cpy_r_left, PyObject *cpy_r_right);
    PyObject *(*CPyDef_project___main____normalize_solidity_version)(PyObject *cpy_r_version);
    char (*CPyDef_project___main____solidity_compiler_equal)(PyObject *cpy_r_config, PyObject *cpy_r_build);
    char (*CPyDef_project___main____vyper_compiler_equal)(PyObject *cpy_r_config, PyObject *cpy_r_build);
    PyObject *(*CPyDef_project___main____load_sources)(PyObject *cpy_r_project_path, PyObject *cpy_r_subfolder, char cpy_r_allow_json);
    char (*CPyDef_project___main____stream_download)(PyObject *cpy_r_download_url, PyObject *cpy_r_target_path, PyObject *cpy_r_headers);
    PyObject *(*CPyDef_project___main____get_mix_default_branch)(PyObject *cpy_r_mix_name, PyObject *cpy_r_headers);
    char (*CPyDef_project___main_____top_level__)(void);
    PyObject **CPyStatic_scripts____FunctionDef;
    PyObject **CPyStatic_scripts____Import;
    PyObject **CPyStatic_scripts____ImportFrom;
    PyObject **CPyStatic_scripts____Path;
    PyObject **CPyStatic_scripts____FunctionType;
    PyObject **CPyStatic_scripts____parse;
    PyObject **CPyStatic_scripts____dump;
    PyObject **CPyStatic_scripts____sha1;
    PyObject **CPyStatic_scripts____import_module;
    PyObject **CPyStatic_scripts____find_spec;
    PyObject **CPyStatic_scripts____reload;
    PyObject **CPyStatic_scripts____DOT_PATH;
    PyObject **CPyStatic_scripts____import_cache;
    PyObject *(*CPyDef_scripts___run)(PyObject *cpy_r_script_path, PyObject *cpy_r_method_name, PyObject *cpy_r_args, PyObject *cpy_r_kwargs, PyObject *cpy_r_project, char cpy_r__include_frame);
    tuple_T2OO (*CPyDef_scripts____get_path)(PyObject *cpy_r_path_str);
    PyObject *(*CPyDef_scripts____import_from_path)(PyObject *cpy_r_path);
    PyObject *(*CPyDef_scripts____get_ast_hash)(PyObject *cpy_r_path);
    char (*CPyDef_scripts_____top_level__)(void);
    PyTypeObject **CPyType_sources___Sources;
    PyObject *(*CPyDef_sources___Sources)(PyObject *cpy_r_contract_sources, PyObject *cpy_r_interface_sources);
    char (*CPyDef_sources___Sources_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_contract_sources, PyObject *cpy_r_interface_sources);
    PyObject *(*CPyDef_sources___Sources___get)(PyObject *cpy_r_self, PyObject *cpy_r_key);
    PyObject *(*CPyDef_sources___Sources___get_path_list)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_sources___Sources___get_contract_list)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_sources___Sources___get_interface_list)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_sources___Sources___get_interface_hashes)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_sources___Sources___get_interface_sources)(PyObject *cpy_r_self);
    PyObject *(*CPyDef_sources___Sources___get_source_path)(PyObject *cpy_r_self, PyObject *cpy_r_contract_name, char cpy_r_is_interface);
    char (*CPyDef_sources___is_inside_offset)(PyObject *cpy_r_inner, PyObject *cpy_r_outer);
    PyObject *(*CPyDef_sources___highlight_source)(PyObject *cpy_r_source, PyObject *cpy_r_offset, CPyTagged cpy_r_pad);
    PyObject *(*CPyDef_sources___get_contract_names)(PyObject *cpy_r_full_source);
    PyObject *(*CPyDef_sources___get_pragma_spec)(PyObject *cpy_r_source, PyObject *cpy_r_path);
    PyObject *(*CPyDef_sources___get_vyper_pragma_spec)(PyObject *cpy_r_source, PyObject *cpy_r_path);
    char (*CPyDef_sources_____top_level__)(void);
    PyObject **CPyStatic_brownie___utils___color;
    PyObject **CPyStatic_brownie___utils___bytes_to_hexstring;
    PyObject **CPyStatic_brownie___utils___hexbytes_to_hexstring;
    char (*CPyDef_brownie___utils_____top_level__)(void);
    PyObject **CPyStatic__color___formatter;
    PyObject **CPyStatic__color___MODIFIERS;
    PyObject **CPyStatic__color___COLORS;
    PyObject **CPyStatic__color___NOTIFY_COLORS;
    PyObject **CPyStatic__color___base_path;
    PyObject **CPyStatic__color___Color_____cache__;
    PyObject **CPyStatic__color___brownie___utils____color___Color___highlight___lexer;
    PyTypeObject **CPyType__color___Color;
    PyObject *(*CPyDef__color___Color)(void);
    PyObject *(*CPyDef__color___Color_____call__)(PyObject *cpy_r_self, PyObject *cpy_r_color_str);
    PyObject *(*CPyDef__color___Color_____str__)(PyObject *cpy_r_self);
    PyObject *(*CPyDef__color___Color___pretty_dict)(PyObject *cpy_r_self, PyObject *cpy_r_value, CPyTagged cpy_r__indent);
    PyObject *(*CPyDef__color___Color___pretty_sequence)(PyObject *cpy_r_self, PyObject *cpy_r_value, CPyTagged cpy_r__indent);
    PyObject *(*CPyDef__color___Color____write)(PyObject *cpy_r_self, PyObject *cpy_r_value);
    PyObject *(*CPyDef__color___Color___format_tb)(PyObject *cpy_r_self, PyObject *cpy_r_exc, PyObject *cpy_r_filename, PyObject *cpy_r_start, PyObject *cpy_r_stop);
    PyObject *(*CPyDef__color___Color___format_syntaxerror)(PyObject *cpy_r_self, PyObject *cpy_r_exc);
    PyObject *(*CPyDef__color___Color___highlight)(PyObject *cpy_r_self, PyObject *cpy_r_text, PyObject *cpy_r_lexer);
    char (*CPyDef__color___Color_____mypyc_defaults_setup)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef__color___notify)(PyObject *cpy_r_type_, PyObject *cpy_r_msg);
    char (*CPyDef__color_____top_level__)(void);
    PyObject *(*CPyDef_output___build_tree)(PyObject *cpy_r_tree_structure, CPyTagged cpy_r_multiline_pad, PyObject *cpy_r_pad_depth, PyObject *cpy_r__indent_data);
    char (*CPyDef_output_____top_level__)(void);
    PyObject **CPyStatic_sql___dumps;
    PyObject **CPyStatic_sql___loads;
    PyTypeObject **CPyType_sql___Cursor;
    PyObject *(*CPyDef_sql___Cursor)(PyObject *cpy_r_filename);
    char (*CPyDef_sql___Cursor_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_filename);
    char (*CPyDef_sql___Cursor___connect)(PyObject *cpy_r_self, PyObject *cpy_r_filename);
    char (*CPyDef_sql___Cursor___insert)(PyObject *cpy_r_self, PyObject *cpy_r_table, PyObject *cpy_r_values);
    char (*CPyDef_sql___Cursor___execute)(PyObject *cpy_r_self, PyObject *cpy_r_cmd, PyObject *cpy_r_args);
    PyObject *(*CPyDef_sql___Cursor___fetchone)(PyObject *cpy_r_self, PyObject *cpy_r_cmd, PyObject *cpy_r_args);
    PyObject *(*CPyDef_sql___Cursor___fetchall)(PyObject *cpy_r_self, PyObject *cpy_r_cmd, PyObject *cpy_r_args);
    char (*CPyDef_sql___Cursor___close)(PyObject *cpy_r_self);
    char (*CPyDef_sql_____top_level__)(void);
    PyObject **CPyStatic_toposort____reduce;
    PyTypeObject **CPyType_toposort___CircularDependencyError;
    PyTypeObject **CPyType_toposort___toposort_gen;
    PyObject *(*CPyDef_toposort___toposort_gen)(void);
    char (*CPyDef_toposort___CircularDependencyError_____init__)(PyObject *cpy_r_self, PyObject *cpy_r_data);
    PyObject *(*CPyDef_toposort___toposort_gen_____mypyc_generator_helper__)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_toposort___toposort_gen_____next__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_toposort___toposort_gen___send)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_arg);
    PyObject *(*CPyDef_toposort___toposort_gen_____iter__)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_toposort___toposort_gen___throw)(PyObject *cpy_r___mypyc_self__, PyObject *cpy_r_type, PyObject *cpy_r_value, PyObject *cpy_r_traceback);
    PyObject *(*CPyDef_toposort___toposort_gen___close)(PyObject *cpy_r___mypyc_self__);
    PyObject *(*CPyDef_toposort___toposort)(PyObject *cpy_r_data);
    PyObject *(*CPyDef_toposort___toposort_flatten)(PyObject *cpy_r_data, char cpy_r_sort);
    char (*CPyDef_toposort_____top_level__)(void);
};
#endif
