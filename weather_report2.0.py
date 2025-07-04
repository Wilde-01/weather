import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QLineEdit,
                             QVBoxLayout, QHBoxLayout, QStackedLayout, QMainWindow,
                             QDialog, QScrollArea, QTextEdit)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
import requests
import datetime

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 如需AI助手功能请安装openai库
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def timestamp_to_beijing_time(timestamp):
    beijing_timezone = datetime.timezone(datetime.timedelta(hours=8))
    beijing_time = datetime.datetime.fromtimestamp(timestamp, tz=beijing_timezone)
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S')

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WeatherAPI:
    def __init__(self, api_key, language='zh_cn'):
        self.api_key = api_key
        self.language = language
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def get_weather(self, city):
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric",
            "lang": self.language
        }
        try:
            response = self.session.get(f"{self.base_url}/weather", params=params, timeout=10)  # , proxies=self.proxies
            if response.status_code == 200:
                return response.json()
            else:
                print(f"天气API请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取天气数据时发生异常: {str(e)}\n请检查网络连接，或稍后重试。")
            return None

    def get_city_coordinates(self, city):
        data = self.get_weather(city)
        if data and 'coord' in data:
            return (data['coord']['lat'], data['coord']['lon'])
        return (None, None)

    def get_weather_forecast(self, lat, lon):
        if None in (lat, lon):
            print("⚠️ 错误：缺少经纬度坐标")
            return None
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": self.language,
            "cnt": 40
        }
        try:
            response = self.session.get(f"{self.base_url}/forecast", params=params, timeout=15)  # , proxies=self.proxies
            if response.status_code == 200:
                return response.json()
            else:
                print(f"预报API请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取预报数据时发生异常: {str(e)}\n请检查网络连接，或稍后重试。")
            return None
class Window1(QMainWindow):
    """综合天气信息窗口"""
    def __init__(self, weather_data, forecast_data):
        super().__init__()
        weather_desc = weather_data['weather'][0]['description'] if weather_data['weather'] else "未知"
        temp = weather_data['main']['temp']
        feels_like = weather_data['main']['feels_like']
        wind_speed = weather_data['wind']['speed']
        wind_deg = weather_data['wind']['deg']   
        pressure = weather_data['main']['pressure']
        humidity = weather_data['main']['humidity']
        sunrise = timestamp_to_beijing_time(weather_data['sys']['sunrise'])
        sunset = timestamp_to_beijing_time(weather_data['sys']['sunset'])
        city = weather_data.get('name', '')
        label_text = (
            f"城市: {city}\n"
            f"当前气温: {temp}℃\n"
            f"体感温度: {feels_like}℃\n"
            f"当前天气: {weather_desc}\n"
            f"风速: {wind_speed} m/s\n"
            f"风向: {wind_deg}°\n"
            f"气压: {pressure} hPa\n"
            f"湿度: {humidity}%\n"
            f"日出时间: {sunrise}\n"
            f"日落时间: {sunset}"
        )
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.setCentralWidget(label)

class Window6(QMainWindow):
    def __init__(self, weather_data, forecast_data):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        title_label = QLabel("未来5天天气预报")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50; margin: 15px 0; text-align: center;")
        layout.addWidget(title_label)
        if weather_data and 'name' in weather_data:
            city_label = QLabel(f"城市: {weather_data['name']}")
            city_label.setStyleSheet("font-size: 22px; color: #3498db; margin-bottom: 15px; text-align: center;")
            layout.addWidget(city_label)
        if forecast_data and 'list' in forecast_data:
            forecasts_by_date = {}
            for forecast in forecast_data['list']:
                dt = datetime.datetime.fromtimestamp(forecast['dt'], datetime.timezone(datetime.timedelta(hours=8)))
                date_str = dt.strftime('%Y-%m-%d')
                if date_str not in forecasts_by_date:
                    forecasts_by_date[date_str] = []
                forecasts_by_date[date_str].append(forecast)
            sorted_dates = sorted(forecasts_by_date.keys())
            for i, date_str in enumerate(sorted_dates):
                if i >= 7:
                    break
                forecasts = forecasts_by_date[date_str]
                temps = [f['main']['temp'] for f in forecasts]
                max_temp = max(temps)
                min_temp = min(temps)
                day_temps = [f['main']['temp'] for f in forecasts if 6 <= datetime.datetime.fromtimestamp(f['dt']).hour <= 18]
                night_temps = [f['main']['temp'] for f in forecasts if datetime.datetime.fromtimestamp(f['dt']).hour < 6 or datetime.datetime.fromtimestamp(f['dt']).hour > 18]
                day_max = max(day_temps) if day_temps else max_temp
                night_min = min(night_temps) if night_temps else min_temp
                noon_forecast = None
                for f in forecasts:
                    forecast_hour = datetime.datetime.fromtimestamp(f['dt']).hour
                    if 11 <= forecast_hour <= 13:
                        noon_forecast = f
                        break
                if noon_forecast is None:
                    noon_forecast = forecasts[len(forecasts) // 2]
                weather_desc = noon_forecast['weather'][0]['description'] if 'weather' in noon_forecast else "未知"
                feels_like = noon_forecast['main']['feels_like'] if 'main' in noon_forecast else "N/A"
                humidity = noon_forecast['main']['humidity'] if 'main' in noon_forecast else "N/A"
                wind_speed = noon_forecast.get('wind', {}).get('speed', 'N/A')
                wind_deg = noon_forecast.get('wind', {}).get('deg', 'N/A')
                pop = int(noon_forecast.get('pop', 0) * 100)
                date_dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_dt.weekday()]
                date_label = QLabel(f"{date_str} ({weekday})")
                date_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: #3498db; color: white; padding: 8px; border-radius: 5px;")
                layout.addWidget(date_label)
                card = QWidget()
                card.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; padding: 15px; margin: 5px 0 20px 0; border: 1px solid #e0e0e0;")
                card_layout = QVBoxLayout(card)
                weather_row = QWidget()
                weather_row_layout = QHBoxLayout(weather_row)
                icon_label = QLabel()
                icon_label.setFixedSize(64, 64)
                icon_label.setStyleSheet("background-color: #e0e7ef; border-radius: 10px;")
                if 'weather' in noon_forecast and noon_forecast['weather']:
                    icon_code = noon_forecast['weather'][0]['icon']
                    icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                    try:
                        response = requests.get(icon_url)
                        if response.status_code == 200:
                            pixmap = QPixmap()
                            pixmap.loadFromData(response.content)
                            icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio))
                    except:
                        pass
                weather_row_layout.addWidget(icon_label)
                desc_label = QLabel(weather_desc)
                desc_label.setStyleSheet("font-size: 22px; font-weight: bold;")
                weather_row_layout.addWidget(desc_label)
                weather_row_layout.addStretch()
                card_layout.addWidget(weather_row)
                from PyQt5.QtWidgets import QGridLayout
                temp_layout = QGridLayout()
                temp_layout.setHorizontalSpacing(20)
                temp_layout.setVerticalSpacing(10)
                temp_layout.addWidget(QLabel("🌡️ 最高温度:"), 0, 0)
                max_temp_label = QLabel(f"{max_temp:.1f}℃")
                max_temp_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #e74c3c;")
                temp_layout.addWidget(max_temp_label, 0, 1)
                temp_layout.addWidget(QLabel("🌡️ 最低温度:"), 0, 2)
                min_temp_label = QLabel(f"{min_temp:.1f}℃")
                min_temp_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3498db;")
                temp_layout.addWidget(min_temp_label, 0, 3)
                temp_layout.addWidget(QLabel("🌡️ 体感温度:"), 1, 0)
                feels_label = QLabel(f"{feels_like:.1f}℃")
                feels_label.setStyleSheet("font-size: 20px;")
                temp_layout.addWidget(feels_label, 1, 1)
                temp_layout.addWidget(QLabel("💧 湿度:"), 1, 2)
                humidity_label = QLabel(f"{humidity}%")
                humidity_label.setStyleSheet("font-size: 20px;")
                temp_layout.addWidget(humidity_label, 1, 3)
                temp_layout.addWidget(QLabel("🌧️ 降水概率:"), 2, 0)
                pop_label = QLabel(f"{pop}%")
                pop_label.setStyleSheet("font-size: 20px;")
                temp_layout.addWidget(pop_label, 2, 1)
                temp_layout.addWidget(QLabel("🌬️ 风速:"), 2, 2)
                wind_label = QLabel(f"{wind_speed} m/s")
                wind_label.setStyleSheet("font-size: 20px;")
                temp_layout.addWidget(wind_label, 2, 3)
                card_layout.addLayout(temp_layout)
                layout.addWidget(card)
        else:
            error_label = QLabel("无法获取天气预报数据")
            error_label.setStyleSheet("font-size: 20px; color: red; text-align: center; margin: 20px;")
            layout.addWidget(error_label)
            if not forecast_data:
                debug_label = QLabel("API响应为空")
                debug_label.setStyleSheet("color: #666; font-family: monospace; text-align: center;")
                layout.addWidget(debug_label)
            elif 'list' not in forecast_data:
                debug_label = QLabel("API响应格式不正确，缺少'list'字段")
                debug_label.setStyleSheet("color: #666; font-family: monospace; text-align: center;")
                layout.addWidget(debug_label)
                debug_text = QLabel(f"响应片段: {str(forecast_data)[:200]}...")
                debug_text.setStyleSheet("color: #666; font-family: monospace; text-align: center;")
                layout.addWidget(debug_text)
        layout.addStretch()
        scroll.setWidget(content)
        self.setCentralWidget(scroll)

class AssistantDialog(QDialog):
    def __init__(self, weather_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能助手")
        self.setFixedSize(850, 750)  
        self.weather_data = weather_data
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 顶部标题
        title = QLabel("🌟 智能天气助手")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
            letter-spacing: 2px;
        """)
        self.layout.addWidget(title)

        # 聊天区域
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            font-size: 18px;
            background: #f7fbff;
            padding: 18px;
            border-radius: 15px;
            border: 1.5px solid #d0e6fa;
            min-height: 300px;
            margin-bottom: 10px;
        """)
        self.layout.addWidget(self.chat_area)

        # 输入区域
        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("请输入你的问题（如：今天适合穿什么？）")
        self.input_line.setStyleSheet("""
            font-size: 18px;
            padding: 12px;
            border-radius: 10px;
            border: 1.5px solid #b2bec3;
            background: #fafdff;
        """)
        input_layout.addWidget(self.input_line)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedHeight(40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(self.send_btn)
        self.layout.addLayout(input_layout)

        self.append_message("AI助手", "正在生成穿衣建议，请稍候...")
        self.ask_ai("请根据以下天气信息，给出详细的穿衣建议。")

    def append_message(self, sender, text):
        # 区分气泡样式
        if sender == "我":
            self.chat_area.append(f"""<div style="text-align: right;">
                <span style="display: inline-block; background: #d1f2eb; color: #16a085; border-radius: 12px; padding: 8px 16px; margin: 4px 0; font-size: 17px;">
                <b>{sender}：</b> {text}
                </span>
            </div>""")
        else:
            self.chat_area.append(f"""<div style="text-align: left;">
                <span style="display: inline-block; background: #eaf6fb; color: #2980b9; border-radius: 12px; padding: 8px 16px; margin: 4px 0; font-size: 17px;">
                <b>{sender}：</b> {text}
                </span>
            </div>""")
    def ask_ai(self, user_question):
        weather_info = (
            f"气温: {self.weather_data['main']['temp']}℃，"
            f"体感温度: {self.weather_data['main']['feels_like']}℃，"
            f"天气: {self.weather_data['weather'][0]['description']}，"
            f"风速: {self.weather_data['wind']['speed']} m/s，"
            f"湿度: {self.weather_data['main']['humidity']}%"
        )
        prompt = f"天气信息：{weather_info}。用户问题：{user_question}"
        if not OPENAI_AVAILABLE:
            self.append_message("AI助手", "未安装openai库，无法使用AI对话功能。请运行 pip install openai 安装。")
            return
        try:
            client = openai.OpenAI(base_url = "https://chatapi.littlewheat.com/v1",
                                   api_key="sk-xAeJYAEBbC2u559HHhs7bZ2M4W1BwJnYdMfhmY8MrGR5oxoD")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个智能天气助手，能结合天气和用户需求给出建议。"},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"出错了：{e}"
        self.append_message("AI助手", answer)
    def on_send(self):
        user_question = self.input_line.text().strip()
        if user_question:
            self.append_message("我", user_question)
            self.input_line.clear()
            self.ask_ai(user_question)

class MyWindow(QWidget):
    def __init__(self, weather_data, forecast_data):
        super().__init__()
        self.weather_data = weather_data
        self.forecast_data = forecast_data
        self.init_ui()
        self.setWindowTitle("智能天气系统")
        try:
            self.setWindowIcon(QIcon(resource_path('weather_icon.png')))
        except:
            pass
        self.setFixedSize(1000, 750)  # 放大主窗口
    def init_ui(self):
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(Window1(self.weather_data, self.forecast_data))  # 索引0 - 综合天气
        self.stacked_layout.addWidget(Window6(self.weather_data, self.forecast_data))  # 索引1 - 天气预报
        container = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(self.stacked_layout)
        widget.setStyleSheet("background-color: #f0f5f9; border-radius: 10px;")
        buttons = [
            ("当前天气", 0),
            ("天气预报", 1),
            ("智能助手", -1),
            ("切换城市", -2)  # 新增
        ]
        btn_container = QHBoxLayout()
        for text, index in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 12px;
                    font-size: 18px;
                    border-radius: 7px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1c6ea4;
                }
            """)
            if text == "智能助手":
                btn.clicked.connect(self.open_assistant)
            elif text == "切换城市":
                btn.clicked.connect(self.switch_city)
            else:
                btn.clicked.connect(lambda _, idx=index: self.stacked_layout.setCurrentIndex(idx))
            btn_container.addWidget(btn)
        container.addWidget(widget)
        container.addLayout(btn_container)
        self.setLayout(container)
        self.setStyleSheet("""
            background-color: white;
            font-family: 'Microsoft YaHei';
        """)
    def open_assistant(self):
        dlg = AssistantDialog(self.weather_data, self)
        dlg.exec_()
    def switch_city(self):
        self.close()
        input_win = InputCityWindow()
        if input_win.exec_() == QDialog.Accepted:
            city_name = input_win.city_name
            api_key = "7e4b65cadd4ad3c1626176cde535055c"
            weather_api = WeatherAPI(api_key)
            weather_data = weather_api.get_weather(city_name)
            if not weather_data:
                error_win = QDialog()
                error_win.setWindowTitle("错误")
                error_win.setFixedSize(500, 300)
                layout = QVBoxLayout()
                error_label = QLabel(f"无法获取{city_name}的天气信息\n请检查城市名称或网络连接")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
                layout.addWidget(error_label)
                retry_btn = QPushButton("重试")
                retry_btn.setStyleSheet("font-size: 16px; padding: 8px;")
                retry_btn.clicked.connect(lambda: sys.exit(1))
                layout.addWidget(retry_btn)
                error_win.setLayout(layout)
                error_win.exec_()
                sys.exit(1)
            lat, lon = weather_api.get_city_coordinates(city_name)
            if lat is None or lon is None:
                print(f"无法获取城市 {city_name} 的经纬度信息")
                sys.exit(1)
            forecast_data = weather_api.get_weather_forecast(lat, lon)
            win = MyWindow(weather_data, forecast_data)
            win.show()
            QApplication.instance().exec_()
        else:
            sys.exit(0)

class InputCityWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.city_name = ""
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("城市查询")
        try:
            self.setWindowIcon(QIcon(resource_path('city_icon.png')))
        except:
            pass
        self.setFixedSize(500, 300)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(30)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.label = QLabel("请输入需要查询的城市名称:")
        self.label.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(self.label)
        city_file = "cityname.txt"
        if os.path.exists(city_file):
            with open(city_file, "r", encoding="utf-8") as file:
                city = file.read().strip()
        else:
            city = ""
        self.city_input = QLineEdit(city, self)
        self.city_input.setPlaceholderText("例如: Beijing, London, Tokyo")
        self.city_input.setStyleSheet("font-size: 20px; padding: 12px;")
        self.layout.addWidget(self.city_input)
        self.btn = QPushButton("查询天气", self)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 12px;
                font-size: 20px;
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.btn.clicked.connect(self.on_button_click)
        self.layout.addWidget(self.btn)
        self.setLayout(self.layout)
    def on_button_click(self):
        self.city_name = self.city_input.text().strip()
        if not self.city_name:
            self.city_input.setPlaceholderText("请输入有效的城市名称!")
            self.city_input.setStyleSheet("font-size: 20px; padding: 12px; background-color: #ffe6e6;")
        else:
            with open("cityname.txt", "w", encoding="utf-8") as file:
                file.write(self.city_name)
            self.accept()

def main():
    app = QApplication(sys.argv)
    input_win = InputCityWindow()
    if input_win.exec_() != QDialog.Accepted:
        sys.exit(0)
    city_name = input_win.city_name
    api_key = "7e4b65cadd4ad3c1626176cde535055c"  # 请确保API密钥有效
    weather_api = WeatherAPI(api_key)
    weather_data = weather_api.get_weather(city_name)
    if not weather_data:
        error_win = QDialog()
        error_win.setWindowTitle("错误")
        error_win.setFixedSize(500, 300)
        layout = QVBoxLayout()
        error_label = QLabel(f"无法获取{city_name}的天气信息\n请检查城市名称或网络连接")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("font-size: 18px; color: #e74c3c;")
        layout.addWidget(error_label)
        retry_btn = QPushButton("重试")
        retry_btn.setStyleSheet("font-size: 16px; padding: 8px;")
        retry_btn.clicked.connect(lambda: sys.exit(1))
        layout.addWidget(retry_btn)
        error_win.setLayout(layout)
        error_win.exec_()
        sys.exit(1)
    coord = weather_data.get('coord', {})
    lat, lon = coord.get('lat'), coord.get('lon')
    if lat is None or lon is None:
        print(f"无法获取城市 {city_name} 的经纬度信息")
        sys.exit(1)
    forecast_data = weather_api.get_weather_forecast(lat, lon)
    win = MyWindow(weather_data, forecast_data)
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()