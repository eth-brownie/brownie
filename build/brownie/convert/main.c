#include <Python.h>

PyMODINIT_FUNC
PyInit_main(void)
{
    PyObject *tmp;
    if (!(tmp = PyImport_ImportModule("42291a5fc61d44f940da__mypyc"))) return NULL;
    PyObject *capsule = PyObject_GetAttrString(tmp, "init_brownie___convert___main");
    Py_DECREF(tmp);
    if (capsule == NULL) return NULL;
    void *init_func = PyCapsule_GetPointer(capsule, "42291a5fc61d44f940da__mypyc.init_brownie___convert___main");
    Py_DECREF(capsule);
    if (!init_func) {
        return NULL;
    }
    return ((PyObject *(*)(void))init_func)();
}

// distutils sometimes spuriously tells cl to export CPyInit___init__,
// so provide that so it chills out
PyMODINIT_FUNC PyInit___init__(void) { return PyInit_main(); }
