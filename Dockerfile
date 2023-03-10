FROM centos/python-38-centos7

ARG BOOK_WEEK_NAME
ARG ID
ARG PSWD
ARG TRUECAPTCHA_USERID
ARG TRUECAPTCHA_APIKEY
ARG WEBHOOK
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY

ENV BOOK_WEEK_NAME $BOOK_WEEK_NAME
ENV ID $ID
ENV PSWD $PSWD
ENV TRUECAPTCHA_USERID $TRUECAPTCHA_USERID
ENV TRUECAPTCHA_APIKEY $TRUECAPTCHA_APIKEY
ENV WEBHOOK $WEBHOOK
ENV AWS_DEFAULT_REGION ap-northeast-1
ENV AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY

USER 0

# install necessary tools
RUN yum install unzip -y
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py

# install headless chrome
RUN curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
RUN yum install google-chrome-stable_current_x86_64.rpm -y

# install traditional chinese font
RUN mkdir -p /usr/share/fonts/chinese/
RUN curl -o /usr/share/fonts/chinese/Noto_Sans_TC.zip https://fonts.google.com/download?family=Noto%20Sans%20TC
RUN cd /usr/share/fonts/chinese/ && unzip Noto_Sans_TC.zip
RUN cd /usr/share/fonts/chinese/ && fc-cache -fv

# install selenium
RUN pip install selenium requests icalendar boto3

# download chromedriver
RUN mkdir /opt/chrome
RUN curl -O https://chromedriver.storage.googleapis.com/110.0.5481.77/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip -d /opt/chrome

VOLUME [ "/screenshots" ]

# for cron #####
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
  systemd-tmpfiles-setup.service ] || rm -f $i; done); \
  rm -f /lib/systemd/system/multi-user.target.wants/*;\
  rm -f /etc/systemd/system/*.wants/*;\
  rm -f /lib/systemd/system/local-fs.target.wants/*; \
  rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
  rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
  rm -f /lib/systemd/system/basic.target.wants/*;\
  rm -f /lib/systemd/system/anaconda.target.wants/*;

VOLUME [ "/sys/fs/cgroup" ]

RUN yum install -y cronie && yum clean all

RUN rm -rf /etc/localtime
RUN ln -s /usr/share/zoneinfo/Singapore /etc/localtime

# for cron #####
RUN crontab -l | { cat; echo "59 23 * * * (cd /app || exit 1; /opt/app-root/bin/python /app/selenium-with-headless-chrome.py > /tmp/app.log)"; } | crontab -
RUN echo BOOK_WEEK_NAME=$BOOK_WEEK_NAME >> /etc/environment
RUN echo ID=$ID >> /etc/environment
RUN echo PSWD=$PSWD >> /etc/environment
RUN echo TRUECAPTCHA_USERID=$TRUECAPTCHA_USERID >> /etc/environment
RUN echo TRUECAPTCHA_APIKEY=$TRUECAPTCHA_APIKEY >> /etc/environment
RUN echo WEBHOOK=$WEBHOOK >> /etc/environment
RUN echo AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION >> /etc/environment
RUN echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> /etc/environment
RUN echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> /etc/environment

WORKDIR /app

# copy the testing python script
COPY selenium-with-headless-chrome.py .
COPY ./notify.tmpl ./notify.tmpl

# CMD [ "python", "selenium-with-headless-chrome.py" ]
CMD ["/usr/sbin/init"]
