#include <Python.h>

PyMODINIT_FUNC
PyInit_scripts(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("b231d8a45f8022bf8159__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie___project___scripts");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "b231d8a45f8022bf8159__mypyc.init_brownie___project___scripts");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit_scripts(); }
