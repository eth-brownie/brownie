#include <Python.h>

PyMODINIT_FUNC
PyInit_pm(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("ccd0f1491df18aed4089__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie____cli___pm");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "ccd0f1491df18aed4089__mypyc.init_brownie____cli___pm");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit_pm(); }
