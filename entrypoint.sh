#!/bin/bash

echo BOOK_WEEK_NAME=$BOOK_WEEK_NAME >> /etc/environment
echo ID=$ID >> /etc/environment
echo PSWD=$PSWD >> /etc/environment
echo TRUECAPTCHA_USERID=$TRUECAPTCHA_USERID >> /etc/environment
echo TRUECAPTCHA_APIKEY=$TRUECAPTCHA_APIKEY >> /etc/environment
echo WEBHOOK=$WEBHOOK >> /etc/environment
echo AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION >> /etc/environment
echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> /etc/environment
echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> /etc/environment
echo BOOK_TIME_IN_REVERSE_ORDER=$BOOK_TIME_IN_REVERSE_ORDER >> /etc/environment

# run systemd
exec /usr/sbin/init