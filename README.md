# 預約羽球場地

1. build docker

* signup [台北市信義運動中心](https://xs.teamxports.com/xs03.aspx?module=login_page&files=login) replace `your-login-id` and `your-secret` accordingly.
* signup [trucaptcha](https://truecaptcha.org/), and replace `truecaptcha-userid`, `truecaptcha-apikey` accordingly.
* setup teams webhook, and replace `teams-webhook-url` accordingly.

```console
docker build \
   --build-arg BOOK_WEEK_NAME="Thursday Friday Saturday Sunday" \
   --build-arg ID=your-login-id \
   --build-arg PSWD='your-secret' \
   --build-arg TRUECAPTCHA_USERID='truecaptcha-userid' \
   --build-arg TRUECAPTCHA_APIKEY='truecaptcha-apikey' \
   --build-arg WEBHOOK='teams-webhook-url' \
   -t xinyi-bot .
```

2. run docker

```console
docker run --rm --name=xinyi-bot --privileged -d -v /tmp/xinyi-bot:/screenshots xinyi-bot
```
