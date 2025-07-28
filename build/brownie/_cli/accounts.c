#include <Python.h>

PyMODINIT_FUNC
PyInit_accounts(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("7e697ddbf4970f222ce8__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie____cli___accounts");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "7e697ddbf4970f222ce8__mypyc.init_brownie____cli___accounts");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit_accounts(); }
