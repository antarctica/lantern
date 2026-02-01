FROM rockylinux/rockylinux:9-minimal

ARG WEB_ROOT=/data/web
ARG ODS_ROOT=$WEB_ROOT/ops-data-store/www/content
ARG CAT_ROOT=$ODS_ROOT/cat

RUN microdnf install -y httpd httpd-tools && \
    microdnf clean all && \
    rm -rf /var/cache/yum

COPY index.html $WEB_ROOT/index.html
RUN mkdir -p $CAT_ROOT && \
    echo 'Trusted content hosting' > $CAT_ROOT/index.html

COPY vhost.conf /etc/httpd/conf.d/ops-data-store.conf
RUN echo "ServerName localhost" > /etc/httpd/conf.d/servername.conf && \
    rm -f /etc/httpd/conf.d/welcome.conf && \
    htpasswd -cb /etc/httpd/.htpasswd user password

EXPOSE 80

CMD ["/usr/sbin/httpd", "-D", "FOREGROUND"]
