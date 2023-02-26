import os
import re
import time
import json
import base64
import platform
import requests

from string import Template

from datetime import timedelta, date, datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import TimeoutException

# calcuate book date, now + 13day
book_date = date.today() + timedelta(days=13)
print('Intent to book %s' % book_date)

# check if the date in desired weekday
# get day of week as an integer, Monday is 0 and Sunday is 6
week = book_date.weekday()
print('Day of a week is %d' % week)

if week in [3, 5, 6, 0, 1, 2]:
    print("It's the date to book")
else:
    print("Skip to book")
    exit()

now = datetime.now()
current_time = now.strftime("%Y-%m-%d-%H-%M-%S")
date_to_book = book_date.strftime("%Y/%m/%d")
date_week_to_book = book_date.strftime("%Y/%m/%d (%A)")

timeout = 10

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-remote-fonts")
chrome_options.add_argument("--lang=zh-TW")

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
    print("%s | Login" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'subform_List')))
    except TimeoutException:
        raise Exception('%s | Login | Timed out waiting for page to load' % driver.title)

    # debug purpose
    # html = driver.page_source
    # print(html)

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
        print('save Login failed')

    # click on login btn
    login_btn = driver.find_element(By.ID, 'login_but')
    login_btn.click()

    print("%s | Login successfully" % driver.title)


def WantBookBadminton():
    print("%s | WantBookBadminton" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_button_image')))
    except TimeoutException:
        raise Exception('%s | WantBookBadminton | Timed out waiting for page to load' % driver.title)

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookBadminton.png' % (screenshots_path, current_time)):
        print('save WantBookBadminton failed')

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[title='羽球']")
    badminton_btn.click()


def AgreeEula():
    print("%s | AgreeEula" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "img[src='img/conf01.png']")))
    except TimeoutException:
        raise Exception('%s | AgreeEula | Timed out waiting for page to load' % driver.title)

    # debug purpose
    if not driver.save_screenshot('%s%s-AgreeEula.png' % (screenshots_path, current_time)):
        print('save AgreeEula failed')

    # click on btn
    badminton_btn = driver.find_element(By.CSS_SELECTOR, "img[src='img/conf01.png']")
    badminton_btn.click()

    # accept alert
    driver.switch_to.alert.accept()


def WantBookDate(date_to_book):
    print("%s | WantBookDate" % driver.title)

    # max retry 30 min
    retry = int((30 * 60) / timeout)

    for i in range(0, retry):
        # wait for page loading
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_StepImage_Lab')))
        except TimeoutException:
            raise Exception('%s | WantBookDate | Timed out waiting for page to load' % driver.title)

        # debug purpose
        print('retry count %d' % i)
        if not driver.save_screenshot('%s%s-WantBookDate.png' % (screenshots_path, current_time)):
            print('save WantBookDate failed')

        # select all "img/NewDataSelect.png"
        btns = driver.find_elements(By.CSS_SELECTOR, "img[src='img/NewDataSelect.png']")
        for btn in btns:
            # print(btn.get_attribute("onclick"))
            if date_to_book in btn.get_attribute("onclick"):
                btn.click()
                # early return
                return

        # pause 10-second, reload page until the desired date is available
        time.sleep(timeout)
        driver.refresh()

    # reach max retry
    raise Exception('%s | WantBookDate | Timed out waiting for desired date %s available' % (driver.title, date_to_book))

def WantBookTime(date_to_book):
    print("%s | WantBookTime" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step2_data')))
    except TimeoutException:
        raise Exception('%s | WantBookTime | Timed out waiting for page to load' % driver.title)

    # debug purpose
    if not driver.save_screenshot('%s%s-WantBookTime.png' % (screenshots_path, current_time)):
        print('save WantBookTime failed')

    # execute script to select afternoon
    driver.execute_script("""
    var date = arguments[0];
    GoToStep2(date, '2');
    """, date_to_book)

    # select all "PlaceBtn"
    btns = driver.find_elements(By.CSS_SELECTOR, "img[name='PlaceBtn']")
    for btn in btns:
        # print(btn.get_attribute("onclick"))
        if '12:00~13:00' in btn.get_attribute("onclick"):
            m = re.search(r'羽.', btn.get_attribute("onclick"))
            print(m.group())
            btn.click()
            # accept alert
            driver.switch_to.alert.accept()
            # early return
            return m.group()


def SaveResult():
    print("%s | SaveResult" % driver.title)

    # wait for page loading
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_Step3Info_lab')))
    except TimeoutException:
        raise Exception('%s | SaveResult | Timed out waiting for page to load' % driver.title)

    if not driver.save_screenshot('%s%s-Result.png' % (screenshots_path, current_time)):
        print('save Result failed')

    return '%s%s-Result.png' % (screenshots_path, current_time)


def NotifyTemplate(tmpl, payload):
    print("%s | Notify" % tmpl)

    url = os.environ['WEBHOOK']

    with open(tmpl, 'r') as f:
        src = Template(f.read())
        result = src.substitute(payload)

        # convert string to dict
        data = json.loads(result)
        # debug purpose
        # print(data)

        response = requests.post(url=url, json=data)
        if response.ok:
            print("%s | Notify successfully" % tmpl)
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

    with open(result_img, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('ascii')
        payload = {
            'date': date_week_to_book,
            'zone': zone,
            'img': encoded_string
        }
        NotifyTemplate("./notify.tmpl/notify.adaptive-card.tmpl", payload)

except Exception as e:
    print('exception: %s' % str(e))
    payload = {
        'date': date_week_to_book,
        'reason': str(e)
    }
    NotifyTemplate("./notify.tmpl/notify.adaptive-card.err.tmpl", payload)


# terminate driver session and close all windows
driver.quit()
