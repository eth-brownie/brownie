#include <Python.h>

PyMODINIT_FUNC
PyInit_console(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("1f6d4040f11363df733c__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie____cli___console");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "1f6d4040f11363df733c__mypyc.init_brownie____cli___console");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit_console(); }
