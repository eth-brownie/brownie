#include <Python.h>

PyMODINIT_FUNC
PyInit__expansion(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("b5e4b1180acefab623dd__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie____expansion");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "b5e4b1180acefab623dd__mypyc.init_brownie____expansion");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit__expansion(); }
