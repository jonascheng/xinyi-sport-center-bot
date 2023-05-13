import os
import re
import time
import json
import boto3
import base64
import platform
import requests
import logging

from string import Template

from datetime import timedelta, date, datetime

from icalendar import Calendar, Event, vCalAddress, vText
from botocore.exceptions import ClientError

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException


# constant variables
DESIRED_BOOK_DT_START_HOUR = 12
DESIRED_BOOK_DT_END_HOUR = 13
DESIRED_BOOK_TIMESLOT = '%d:00~%d:00' % (DESIRED_BOOK_DT_START_HOUR, DESIRED_BOOK_DT_END_HOUR)
BUCKET_NAME = 'txone-badminton-ical'

# calcuate book date, now() + 13day
now = datetime.now()
current_time = now.strftime("%Y-%m-%d-%H-%M-%S")
book_date = date.today() + timedelta(days=13)
if now.hour >= 23 and now.minute >= 55:
    # calcuate book date, now(23:5x) + 14day
    book_date = date.today() + timedelta(days=14)

# init a logger that will be used to log in a file /tmp/app.log as well as stdout
logger = logging.getLogger()
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
fileHandler = logging.FileHandler("/tmp/app-%s.log" % current_time)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)


logger.info('Current time is %s' % current_time)
logger.info('Intent to book %s' % book_date)

# check if the date in desired weekday
# get day of week as an integer, Monday is 0 and Sunday is 6
week = book_date.weekday()
# convert to week name
week_name = book_date.strftime("%A")
logger.info('Day of a week is %s' % week_name)
desired_book_week_name = os.environ.get('BOOK_WEEK_NAME', "Thursday")
book_time_in_reverse_order = (os.environ.get('BOOK_TIME_IN_REVERSE_ORDER', 'False') == 'True')

logger.info('Day of a week is desired to book %s (env: BOOK_WEEK_NAME)' % desired_book_week_name)
if week_name.lower() in desired_book_week_name.lower():
    logger.info("It's the date to book")
else:
    logger.info("Skip to book")
    exit()

date_to_book = book_date.strftime("%Y/%m/%d")
date_week_to_book = book_date.strftime("%Y/%m/%d (%A)")

timeout = 5

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-remote-fonts")
chrome_options.add_argument("--lang=zh-TW")
chrome_options.add_argument("--window-size=1024,1024")

screenshots_path = '/screenshots/'
if platform.system() == 'Windows':
  driver = webdriver.Chrome(r'chromedriver', chrome_options=chrome_options)
  screenshots_path = 'c:\\windows\\temp\\'
else:
  driver = webdriver.Chrome(r'/opt/chrome/chromedriver', chrome_options=chrome_options)

driver.fullscreen_window()
driver.get("https://xs.teamxports.com/xs03.aspx?module=login_page&files=login")
# accept alert all the time
driver.switch_to.alert.accept()


def GeneratePresignedURL(zone):
    # the object name to upload and 30 days in second to expire
    expiration = 30*24*60*60
    object_name = '%s.ics' % current_time

    cal = Calendar()

    event = Event()
    event.add('summary', '羽球社團活動')
    event.add('dtstart', datetime(book_date.year, book_date.month, book_date.day, DESIRED_BOOK_DT_START_HOUR, 0, 0))
    event.add('dtend', datetime(book_date.year, book_date.month, book_date.day, DESIRED_BOOK_DT_END_HOUR, 0, 0))
    event.add('dtstamp', datetime(book_date.year, book_date.month, book_date.day, 0, 0, 0))

    organizer = vCalAddress('MAILTO:hatsune@txone.com')
    organizer.params['cn'] = vText('Hatsune Miku')
    organizer.params['role'] = vText('Assistant')

    event['organizer'] = organizer
    event['location'] = vText('信義運動中心 %s' % zone)

    # Adding events to calendar and generate ical
    cal.add_component(event)
    event_ics = '%s%s' % ('/tmp/', object_name)
    logger.info("ics file will be generated at %s" % event_ics)
    with open(event_ics, 'wb') as ics:
        ics.write(cal.to_ical())

    # upload ical
    s3_client = boto3.client("s3")
    try:
        response = s3_client.upload_file(event_ics, BUCKET_NAME, object_name)
    except ClientError as e:
        logger.error('upload ical to S3 failed: %s' % str(e))
        return ""

    # generate presigned url
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logger.error('generate presigned failed: %s' % str(e))
        return ""

    return response


def CaptchaImg2Text(captcha_img, userid, apikey):
    with open(captcha_img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        url = 'https://api.apitruecaptcha.org/one/gettext'

        data = {
            'userid': userid,
            'apikey': apikey,
            'data': encoded_string
        }
        response = requests.post(url=url, json=data)
        data = response.json()
        return data


def Login():
    logger.info("%s | Login" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'subform_List')))
    except TimeoutException:
        raise Exception('%s | Login | Timed out waiting for page to load' % driver.title)

    # debug purpose
    # html = driver.page_source
    # logger.info(html)

    # download captcha
    img_base64 = driver.execute_script("""
    var ele = arguments[0];
    var cnv = document.createElement('canvas');
    cnv.width = ele.width; cnv.height = ele.height;
    cnv.getContext('2d').drawImage(ele, 0, 0);
    return cnv.toDataURL('image/jpeg').substring(22);
    """, driver.find_element(By.ID, 'ContentPlaceHolder1_CaptchaImage'))

    captcha_img = '%s%s-captcha.png' % (screenshots_path, current_time)
    with open(captcha_img, 'wb') as image:
        image.write(base64.b64decode(img_base64))

    # convert Img to Text
    jsonData = CaptchaImg2Text(captcha_img, os.environ['TRUECAPTCHA_USERID'], os.environ['TRUECAPTCHA_APIKEY'])
    if 'result' in jsonData:
        captchaText = jsonData['result']
    else:
        raise Exception('%s | Login | Fail to convert captcha to text with unexpected response %s' % (driver.title, jsonData))

    # input login id
    login_id_input = driver.find_element(By.ID, 'ContentPlaceHolder1_loginid')
    login_id_input.send_keys(os.environ['ID'])

    # input password
    password_input = driver.find_element(By.ID, 'loginpw')
    password_input.send_keys(os.environ['PSWD'])

    # input captcha
    captcha_input = driver.find_element(By.ID, 'ContentPlaceHolder1_Captcha_text')
    captcha_input.send_keys(captchaText)

    # debug purpose
    if not driver.save_screenshot('%s%s-Login.png' % (screenshots_path, current_time)):
        logger.error('%s | Login | Save Login failed' % driver.title)

    # click on login btn
    login_btn = driver.find_element(By.ID, 'login_but')
    login_btn.click()

    logger.info("%s | Login successfully" % driver.title)


def WantBookBadminton():
    logger.info("%s | WantBookBadminton" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_button_image')))
    except TimeoutException:
        raise Exception('%s | WantBookBadminton | Timed out waiting for page to load' % driver.title)

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookBadminton.png' % (screenshots_path, current_time)):
        logger.error('%s | WantBookBadminton | Save WantBookBadminton failed' % driver.title)

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[title='羽球']")
    badminton_btn.click()


def AgreeEula():
    logger.info("%s | AgreeEula" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[src='img/conf01.png']")))
    except TimeoutException:
        raise Exception('%s | AgreeEula | Timed out waiting for page to load' % driver.title)

    # debug purpose
    if not driver.save_screenshot('%s%s-AgreeEula.png' % (screenshots_path, current_time)):
        logger.error('%s | AgreeEula | Save AgreeEula failed' % driver.title)

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[src='img/conf01.png']")
    badminton_btn.click()

    # accept alert
    driver.switch_to.alert.accept()


def adaptiveSleep():
    # min sleep 0.1 sec
    sleep = 0.1

    # calcuate adaptive sleep interval, wake up at 00:00:00 as possible
    if now.hour >= 23 and now.minute >= 55:
        target_time = datetime(now.year, now.month, now.day+1, 0, 0, 0)
        current_time = datetime.now()
        sleep = (target_time - current_time).total_seconds()

    logger.info("Adaptive sleep %f sec" % sleep)
    time.sleep(sleep)


def WantBookDate(date_to_book):
    logger.info("%s | WantBookDate" % driver.title)

    # max retry 60 times
    retry = 60

    for i in range(0, retry):
        # wait for page loading
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_StepImage_Lab')))
        except TimeoutException:
            raise Exception('%s | WantBookDate | Timed out waiting for page to load' % driver.title)

        # debug purpose
        logger.info('%s | WantBookDate | Retry count %d' % (driver.title, i))
        # if not driver.save_screenshot('%s%s-WantBookDate.png' % (screenshots_path, current_time)):
        #     logger.error('%s | WantBookDate | Save WantBookDate failed' % driver.title)
        # logger.info('%s | WantBookDate | (%d) %s%s-WantBookDate.png was saved' % (driver.title, i, screenshots_path, current_time))

        # select all "img/NewDataSelect.png"
        btns = driver.find_elements(By.CSS_SELECTOR, "img[src='img/NewDataSelect.png']")
        for btn in btns:
            # logger.info(btn.get_attribute("onclick"))
            if date_to_book in btn.get_attribute("onclick"):
                btn.click()
                logger.info("%s | WantBookDate | %s was selected" % (driver.title, date_to_book))
                # early return
                return

        # pause and reload page until the desired date is available
        # time.sleep(sleep)
        adaptiveSleep()
        driver.refresh()

    # reach max retry
    raise Exception('%s | WantBookDate | Timed out waiting for desired date %s available' % (driver.title, date_to_book))


def WantBookTime(date_to_book):
    logger.info("%s | WantBookTime" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step2_data')))
    except TimeoutException:
        raise Exception('%s | WantBookTime | Timed out waiting for page to load' % driver.title)

    # debug purpose
    # if not driver.save_screenshot('%s%s-WantBookTime1.png' % (screenshots_path, current_time)):
    #     logger.error('%s | WantBookTime | Save WantBookTime failed' % driver.title)
    # logger.info('%s | WantBookTime | %s%s-WantBookTime1.png was saved' % (driver.title, screenshots_path, current_time))

    # execute script to select afternoon
    driver.execute_script("""
    var date = arguments[0];
    GoToStep2(date, '2');
    """, date_to_book)
    logger.info("%s | WantBookTime | %s afternoon was selected" % (driver.title, date_to_book))

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookTime2.png' % (screenshots_path, current_time)):
        logger.error('%s | WantBookTime | Save WantBookTime failed' % driver.title)
    logger.info('%s | WantBookTime | %s%s-WantBookTime2.png was saved' % (driver.title, screenshots_path, current_time))

    # select all "PlaceBtn"
    btns = driver.find_elements(By.CSS_SELECTOR, "img[name='PlaceBtn']")
    # loop through all btns in reverse order
    if book_time_in_reverse_order:
        logger.info("%s | WantBookTime | Book time in reverse order" % driver.title)
        btns.reverse()
    for btn in btns:
        # logger.info(btn.get_attribute("onclick"))
        if DESIRED_BOOK_TIMESLOT in btn.get_attribute("onclick"):
            m = re.search(r'羽.', btn.get_attribute("onclick"))
            logger.info('%s | WantBookTime | Intent to select %s ' % (driver.title, m.group()))
            btn.click()
            # accept alert
            driver.switch_to.alert.accept()
            logger.info('%s | WantBookTime | %s was selected' % (driver.title, m.group()))
            # early return
            return m.group()


def SaveResult():
    logger.info("%s | SaveResult" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step3Info_lab')))
    except TimeoutException:
        raise Exception('%s | SaveResult | Timed out waiting for page to load' % driver.title)

    if not driver.save_screenshot('%s%s-Result.png' % (screenshots_path, current_time)):
        logger.error('%s | SaveResult | Save Result failed' % driver.title)

    return '%s%s-Result.png' % (screenshots_path, current_time)


def SaveLastScreen():
    logger.info("%s | SaveLastScreen" % driver.title)

    if not driver.save_screenshot('%s%s-SaveLastScreen.png' % (screenshots_path, current_time)):
        logger.error('%s | SaveLastScreen | Save SaveLastScreen failed' % driver.title)

    return '%s%s-SaveLastScreen.png' % (screenshots_path, current_time)


def NotifyTemplate(tmpl, payload):
    logger.info("%s | Notify" % tmpl)

    url = os.environ['WEBHOOK']

    with open(tmpl, 'r') as f:
        src = Template(f.read())
        result = src.substitute(payload)

        # convert string to dict
        data = json.loads(result)
        # debug purpose
        # logger.info(data)

        response = requests.post(url=url, json=data)
        if response.ok:
            logger.info("%s | Notify successfully" % tmpl)
        else:
            requests.raise_for_status()


try:
    # login page
    Login()
    # want book badminton
    WantBookBadminton()
    # agress eula
    AgreeEula()
    # want book date
    WantBookDate(date_to_book)
    # want book time
    zone = WantBookTime(date_to_book)
    # save result
    result_img = SaveResult()
    # generate ical link
    ical_url = GeneratePresignedURL(zone)

    with open(result_img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        payload = {
            'date': date_week_to_book,
            'time': DESIRED_BOOK_TIMESLOT,
            'zone': zone,
            'img': encoded_string,
            'ical_url': ical_url
        }
        NotifyTemplate("./notify.tmpl/notify.adaptive-card.tmpl", payload)

except Exception as e:
    logger.error('Exception: %s' % str(e))

    # save last error screen
    result_img = SaveLastScreen()

    with open(result_img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        payload = {
            'date': date_week_to_book,
            'time': DESIRED_BOOK_TIMESLOT,
            'reason': str(e),
            'img': encoded_string
        }
        NotifyTemplate("./notify.tmpl/notify.adaptive-card.err.tmpl", payload)


# terminate driver session and close all windows
driver.quit()
