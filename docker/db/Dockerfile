ARG MYSQL_VERSION
FROM mysql:${MYSQL_VERSION}

#ADD ./mysql-init-files /docker-entrypoint-initdb.d
#####################################
# Set Timezone
#####################################

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && chown -R mysql:root /var/lib/mysql/

COPY ./docker/db/my.cnf /etc/mysql/conf.d/my.cnf
RUN chmod 0444 /etc/mysql/conf.d/my.cnf

CMD ["mysqld"]

EXPOSE 3306
