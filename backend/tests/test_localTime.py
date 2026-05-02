"""
本地时间工具模块的单元测试
测试UTC时间转换为本地时间的功能
"""
import pytest
from datetime import datetime
import pytz

from app.utils.localTime import convert_utc_to_local_time


class TestConvertUTCToLocalTime:
    """UTC时间转换功能的测试类"""
    
    def test_convert_utc_to_local_time_default(self):
        """测试默认时区转换（UTC转北京时间）"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        assert isinstance(result, datetime)
        # UTC 12:00 应该转换为北京时间 20:00（+8小时）
        assert result.hour == 20
        assert result.day == 7
        assert result.month == 12
        assert result.year == 2023
    
    def test_convert_utc_to_local_time_custom_format(self):
        """测试自定义时间格式"""
        utc_time_str = "2023-12-07 12:00:00"
        result = convert_utc_to_local_time(utc_time_str, strip="%Y-%m-%d %H:%M:%S")
        
        assert isinstance(result, datetime)
        assert result.hour == 20
    
    def test_convert_utc_to_local_time_custom_timezone(self):
        """测试自定义时区"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="UTC")
        
        assert isinstance(result, datetime)
        # UTC时区应该保持时间不变
        assert result.hour == 12
        assert result.day == 7
    
    def test_convert_utc_to_local_time_new_york(self):
        """测试转换到纽约时间"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="America/New_York")
        
        assert isinstance(result, datetime)
        # UTC 12:00 在纽约时间应该是早上7:00（-5小时，不考虑夏令时）
        assert result.hour == 7
        assert result.day == 7
    
    def test_convert_utc_to_local_time_london(self):
        """测试转换到伦敦时间"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="Europe/London")
        
        assert isinstance(result, datetime)
        # UTC和伦敦时间相同（非夏令时期间）
        assert result.hour == 12
        assert result.day == 7
    
    def test_convert_utc_to_local_time_tokyo(self):
        """测试转换到东京时间"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="Asia/Tokyo")
        
        assert isinstance(result, datetime)
        # UTC 12:00 在东京时间应该是21:00（+9小时）
        assert result.hour == 21
        assert result.day == 7
    
    def test_convert_utc_to_local_time_date_change(self):
        """测试跨日期转换"""
        utc_time_str = "2023-12-07T20:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)  # 默认转北京时间
        
        assert isinstance(result, datetime)
        # UTC 20:00 转换为北京时间应该是第二天4:00（+8小时）
        assert result.hour == 4
        assert result.day == 8  # 应该是第二天
        assert result.month == 12
        assert result.year == 2023
    
    def test_convert_utc_to_local_time_negative_timezone(self):
        """测试负时区转换"""
        utc_time_str = "2023-12-07T02:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="America/Los_Angeles")
        
        assert isinstance(result, datetime)
        # UTC 2:00 在洛杉矶时间应该是前一天18:00（-8小时）
        assert result.hour == 18
        assert result.day == 6  # 应该是前一天
    
    def test_convert_utc_to_local_time_milliseconds(self):
        """测试包含毫秒的时间"""
        utc_time_str = "2023-12-07T12:30:45.123456Z"
        result = convert_utc_to_local_time(utc_time_str, strip="%Y-%m-%dT%H:%M:%S.%fZ")
        
        assert isinstance(result, datetime)
        assert result.hour == 20  # +8小时
        assert result.minute == 30
        assert result.second == 45
        assert result.microsecond == 123456
    
    def test_convert_utc_to_local_time_invalid_format(self):
        """测试无效的时间格式"""
        invalid_time_str = "2023-12-07 12:00:00"  # 默认格式不匹配
        
        with pytest.raises(ValueError):
            convert_utc_to_local_time(invalid_time_str)
    
    def test_convert_utc_to_local_time_invalid_timezone(self):
        """测试无效的时区"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        
        with pytest.raises(Exception):  # pytz会抛出异常
            convert_utc_to_local_time(utc_time_str, tz="Invalid/Timezone")
    
    def test_convert_utc_to_local_time_empty_string(self):
        """测试空字符串"""
        with pytest.raises(ValueError):
            convert_utc_to_local_time("")
    
    def test_convert_utc_to_local_time_none_input(self):
        """测试None输入"""
        with pytest.raises((TypeError, AttributeError)):
            convert_utc_to_local_time(None)
    
    def test_convert_utc_to_local_time_edge_case_midnight(self):
        """测试午夜时间转换"""
        # UTC午夜
        utc_time_str = "2023-12-07T00:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        assert isinstance(result, datetime)
        # UTC 0:00 转换为北京时间应该是8:00
        assert result.hour == 8
        assert result.day == 7
        assert result.month == 12
        assert result.year == 2023
    
    def test_convert_utc_to_local_time_edge_case_end_of_day(self):
        """测试一天结束时的转换"""
        # UTC 23:59
        utc_time_str = "2023-12-07T23:59:59.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        assert isinstance(result, datetime)
        # UTC 23:59 转换为北京时间应该是第二天7:59
        assert result.hour == 7
        assert result.minute == 59
        assert result.second == 59
        assert result.day == 8
    
    def test_convert_utc_to_local_time_different_months(self):
        """测试跨月转换"""
        # 月末最后一天的UTC时间
        utc_time_str = "2023-01-31T18:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        assert isinstance(result, datetime)
        # UTC 18:00 转换为北京时间应该是第二天2:00
        assert result.hour == 2
        assert result.day == 1  # 应该是下个月的第一天
        assert result.month == 2
        assert result.year == 2023
    
    def test_convert_utc_to_local_time_leap_year(self):
        """测试闰年转换"""
        # 闰年2月29日
        utc_time_str = "2024-02-29T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        assert isinstance(result, datetime)
        assert result.hour == 20
        assert result.day == 29
        assert result.month == 2
        assert result.year == 2024
    
    def test_convert_utc_to_local_time_short_format(self):
        """测试简短格式"""
        utc_time_str = "20231207T120000Z"
        result = convert_utc_to_local_time(utc_time_str, strip="%Y%m%dT%H%M%SZ")
        
        assert isinstance(result, datetime)
        assert result.hour == 20
        assert result.day == 7
        assert result.month == 12
        assert result.year == 2023
    
    def test_convert_utc_to_local_time_timezone_comparison(self):
        """测试不同时区转换结果对比"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        
        # 转换到不同时区
        beijing_time = convert_utc_to_local_time(utc_time_str, tz="Asia/Shanghai")
        tokyo_time = convert_utc_to_local_time(utc_time_str, tz="Asia/Tokyo")
        utc_time = convert_utc_to_local_time(utc_time_str, tz="UTC")
        london_time = convert_utc_to_local_time(utc_time_str, tz="Europe/London")
        
        # 验证时差
        assert beijing_time.hour == 20
        assert tokyo_time.hour == 21
        assert utc_time.hour == 12
        assert london_time.hour == 12  # 冬季与UTC相同


class TestTimezoneHandling:
    """时区处理测试类"""
    
    def test_timezone_object_creation(self):
        """测试时区对象创建"""
        beijing_tz = pytz.timezone("Asia/Shanghai")
        utc_tz = pytz.timezone("UTC")
        new_york_tz = pytz.timezone("America/New_York")
        
        assert beijing_tz is not None
        assert utc_tz is not None
        assert new_york_tz is not None
    
    def test_timezone_aware_datetime(self):
        """测试时区感知的datetime对象"""
        utc_time_str = "2023-12-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str)
        
        # 验证返回的是时区感知的datetime对象
        assert result.tzinfo is not None
        assert result.tzinfo.zone == "Asia/Shanghai"
    
    def test_dst_handling(self):
        """测试夏令时处理"""
        # 选择一个夏令时期间的时间
        utc_time_str = "2023-07-07T12:00:00.000Z"
        result = convert_utc_to_local_time(utc_time_str, tz="America/New_York")
        
        # 7月是夏令时期间，EDT比UTC晚4小时
        assert result.hour == 8  # 12 - 4 = 8
        assert result.tzinfo.zone == "America/New_York"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])