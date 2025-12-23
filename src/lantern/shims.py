import truststore


def inject_truststore_into_ssl_boto_fix() -> None:
    """
    Extend truststore injection to workaround botocore SSL context recursion error.

    See https://github.com/sethmlarson/truststore/pull/180 for details and workaround source by @mckirk.
    """
    truststore.inject_into_ssl()

    # replace reference kept by botocore as well
    import botocore.httpsession

    botocore.httpsession.SSLContext = truststore.SSLContext  # ty:ignore[unresolved-attribute]
