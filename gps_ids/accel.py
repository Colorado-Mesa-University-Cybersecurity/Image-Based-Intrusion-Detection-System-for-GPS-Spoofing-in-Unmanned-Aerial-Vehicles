BACKENDS = ("auto", "sklearn", "cuml")


class BackendUnavailable(RuntimeError):
    pass


def _check(backend):
    if backend not in BACKENDS:
        raise ValueError(
            "unknown backend %r; valid backends: %s" % (backend, list(BACKENDS))
        )


def _cuml_svc():
    from cuml.svm import SVC

    return SVC


def resolve_svc(backend="auto"):
    _check(backend)
    if backend in ("auto", "cuml"):
        try:
            return "cuml", _cuml_svc()
        except Exception as error:
            if backend == "cuml":
                raise BackendUnavailable(
                    "the cuml backend was requested but cuml could not be "
                    "imported (%s); cuml ships for linux only, so on Windows run "
                    "under WSL2 or pass svc_backend='sklearn'" % error
                )
    from sklearn.svm import SVC

    return "sklearn", SVC


def build_svc(seed, *, class_weight, backend="auto", kernel="rbf"):
    name, cls = resolve_svc(backend)
    if name == "cuml":
        return name, cls(kernel=kernel, class_weight=class_weight, random_state=seed)
    return name, cls(
        kernel=kernel,
        class_weight=class_weight,
        probability=False,
        random_state=seed,
    )
