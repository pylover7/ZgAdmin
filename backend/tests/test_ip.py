"""
IP地址工具模块的单元测试
测试IP地址获取和User-Agent解析功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import ipaddress

from app.utils.ip import getIpAddress, getReqSysBro, SysBro
from fastapi import Request


class TestGetIpAddress:
    """IP地址获取功能的测试类"""
    
    @pytest.mark.asyncio
    async def test_get_private_ip(self):
        """测试获取私有IP地址"""
        result = await getIpAddress("127.0.0.1")
        assert result == "内网IP"
        
        result = await getIpAddress("192.168.1.1")
        assert result == "内网IP"
        
        result = await getIpAddress("10.0.0.1")
        assert result == "内网IP"
        
        result = await getIpAddress("172.16.0.1")
        assert result == "内网IP"
    
    @pytest.mark.asyncio
    async def test_get_public_ip_success_api2(self):
        """测试通过API2成功获取公网IP地址"""
        mock_response = Mock()
        mock_response.content.decode.return_value = '{"data":{"address":"北京市 电信"}}'
        
        with patch('httpx.get', return_value=mock_response):
            result = await getIpAddress("8.8.8.8")
            assert result == "北京市电信"
    
    @pytest.mark.asyncio
    async def test_get_public_ip_success_api1_fallback(self):
        """测试API2失败时使用API1成功获取"""
        # API2失败
        mock_response_api2 = Mock()
        mock_response_api2.content.decode.return_value = '{"error":"not_found"}'
        mock_response_api2.json.side_effect = KeyError("data")
        
        # API1成功
        mock_response_api1 = Mock()
        mock_response_api1.content.decode.return_value = '{"data":[{"location":"上海市 移动"}]}'
        
        with patch('httpx.get') as mock_get:
            mock_get.side_effect = [mock_response_api2, mock_response_api1]
            result = await getIpAddress("8.8.8.8")
            assert result == "上海市移动"
    
    @pytest.mark.asyncio
    async def test_get_public_ip_both_apis_fail(self):
        """测试两个API都失败时返回空字符串"""
        # 两个API都失败
        mock_response = Mock()
        mock_response.content.decode.return_value = '{"error":"not_found"}'
        
        with patch('httpx.get', return_value=mock_response):
            result = await getIpAddress("8.8.8.8")
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_get_public_ip_network_error(self):
        """测试网络请求错误"""
        with patch('httpx.get', side_effect=Exception("Network error")):
            result = await getIpAddress("8.8.8.8")
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_get_public_ip_invalid_json_response(self):
        """测试无效JSON响应"""
        mock_response = Mock()
        mock_response.content.decode.return_value = "invalid json"
        
        with patch('httpx.get', return_value=mock_response):
            result = await getIpAddress("8.8.8.8")
            assert result == ""
    
    def test_get_private_ip_validation(self):
        """测试私有IP地址验证逻辑"""
        # 这些应该被识别为私有IP
        private_ips = [
            "127.0.0.1",
            "127.0.0.0",
            "192.168.0.1",
            "192.168.255.255",
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255"
        ]
        
        # 这些应该被视为公网IP
        public_ips = [
            "8.8.8.8",
            "114.114.114.114",
            "1.1.1.1",
            "223.5.5.5"
        ]
        
        # 验证逻辑（使用ipaddress库）
        for ip in private_ips:
            assert ipaddress.ip_address(ip).is_private, f"{ip} should be private"
        
        for ip in public_ips:
            assert not ipaddress.ip_address(ip).is_private, f"{ip} should be public"
    
    @pytest.mark.asyncio
    async def test_get_ip_address_with_different_formats(self):
        """测试不同格式的IP地址"""
        # IPv6地址（应该被视为公网地址，API可能不支持）
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.content.decode.return_value = '{"data":{"address":"未知位置"}}'
            mock_get.return_value = mock_response
            
            result = await getIpAddress("::1")  # IPv6本地地址
            # IPv6本地地址可能不会被ip_address.is_private识别为私有，但我们的API可能不支持
            # 这里我们主要测试不会抛出异常
            assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_ip_address_api_response_format_variations(self):
        """测试API响应格式变化"""
        # 测试API返回不同格式的地址信息
        test_cases = [
            '{"data":{"address":"广东省深圳市 联通"}}',
            '{"data":{"address":"美国 加利福尼亚"}}',
            '{"data":{"address":"未知地址"}}',
            '{"data":{"address":""}}'
        ]
        
        for response_text in test_cases:
            mock_response = Mock()
            mock_response.content.decode.return_value = response_text
            
            with patch('httpx.get', return_value=mock_response):
                result = await getIpAddress("8.8.8.8")
                assert isinstance(result, str)
                # 空格应该被移除
                assert " " not in result


class TestGetReqSysBro:
    """请求系统和浏览器信息获取的测试类"""
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_normal_chrome(self):
        """测试正常Chrome浏览器User-Agent"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "Windows NT 10.0; Win64; x64"
        assert result.browser == "Chrome"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_firefox(self):
        """测试Firefox浏览器User-Agent"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Firefox/121.0"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "Macintosh; Intel Mac OS X 10_15_7"
        assert result.browser == "Firefox"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_safari(self):
        """测试Safari浏览器User-Agent"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "iPhone; CPU iPhone OS 17_0 like Mac OS X"
        assert result.browser == "Safari"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_edge(self):
        """测试Edge浏览器User-Agent"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "Windows NT 10.0; Win64; x64"
        assert result.browser == "Edg"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_no_user_agent(self):
        """测试没有User-Agent头的情况"""
        mock_request = Mock()
        mock_request.headers.get.return_value = None
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "未知系统"
        assert result.browser == "未知浏览器"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_empty_user_agent(self):
        """测试空User-Agent字符串"""
        mock_request = Mock()
        mock_request.headers.get.return_value = ""
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "未知系统"
        assert result.browser == "未知浏览器"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_unknown_browser(self):
        """测试未知浏览器"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "SomeCustomBrowser/1.0 (Windows NT 10.0; Win64; x64)"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "Windows NT 10.0; Win64; x64"
        assert result.browser == "未知浏览器"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_complex_user_agent(self):
        """测试复杂的User-Agent字符串"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/105.0.0.0"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "X11; Linux x86_64"
        # 会匹配到Chrome，因为我们按顺序检查
        assert result.browser == "Chrome"
    
    @pytest.mark.asyncio
    async def test_get_req_sysbro_multiple_browsers(self):
        """测试包含多个浏览器标识的User-Agent"""
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0 Firefox/121.0"
        
        result = await getReqSysBro(mock_request)
        
        assert isinstance(result, SysBro)
        assert result.system == "Windows NT 10.0; Win64; x64"
        # 应该匹配第一个找到的浏览器（Chrome）
        assert result.browser == "Chrome"


class TestSysBroModel:
    """SysBro模型测试类"""
    
    def test_sysbro_creation(self):
        """测试SysBro对象创建"""
        sys_bro = SysBro(system="Windows 10", browser="Chrome")
        
        assert sys_bro.system == "Windows 10"
        assert sys_bro.browser == "Chrome"
    
    def test_sysbro_empty_data(self):
        """测试空数据的SysBro对象"""
        sys_bro = SysBro(system="", browser="")
        
        assert sys_bro.system == ""
        assert sys_bro.browser == ""
    
    def test_sysbro_serialization(self):
        """测试SysBro对象序列化"""
        sys_bro = SysBro(system="macOS", browser="Safari")
        
        # 测试转换为字典（Pydantic模型支持）
        data = sys_bro.model_dump()
        assert data == {"system": "macOS", "browser": "Safari"}
    
    def test_sysbro_from_dict(self):
        """测试从字典创建SysBro对象"""
        data = {"system": "Linux", "browser": "Firefox"}
        sys_bro = SysBro(**data)
        
        assert sys_bro.system == "Linux"
        assert sys_bro.browser == "Firefox"


class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    async def test_ip_and_user_agent_integration(self):
        """测试IP地址和User-Agent解析的集成"""
        # 模拟一个完整的请求
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # 获取系统和浏览器信息
        sys_bro = await getReqSysBro(mock_request)
        assert isinstance(sys_bro, SysBro)
        assert sys_bro.browser == "Chrome"
        assert "Windows" in sys_bro.system
        
        # 获取IP地址信息（私有IP）
        ip_info = await getIpAddress("192.168.1.1")
        assert ip_info == "内网IP"
    
    @pytest.mark.asyncio
    async def test_real_world_scenario(self):
        """测试真实世界场景"""
        # 模拟一个来自公网IP的用户请求
        mock_request = Mock()
        mock_request.headers.get.return_value = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        
        # 解析User-Agent
        sys_bro = await getReqSysBro(mock_request)
        assert sys_bro.browser == "Safari"
        assert "iPhone" in sys_bro.system
        
        # 获取公网IP信息
        with patch('httpx.get') as mock_get:
            mock_response = Mock()
            mock_response.content.decode.return_value = '{"data":{"address":"北京市 移动"}}'
            mock_get.return_value = mock_response
            
            ip_info = await getIpAddress("114.114.114.114")
            assert "北京" in ip_info and "移动" in ip_info


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])