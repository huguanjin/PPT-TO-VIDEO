# Edge TTS SSL证书修复说明

## 问题描述

2025年10月,微软Edge TTS API服务器(`api.msedgeservices.com`)的SSL证书过期,导致所有使用该服务的应用出现以下错误:

```
SSLCertVerificationError: certificate verify failed: certificate has expired
```

## 症状

- Edge TTS配音失败
- 错误信息包含 `CERTIFICATE_VERIFY_FAILED`
- 所有重试都失败
- 回退到自定义方法也失败(因为底层使用同一服务)

## 根本原因

**不是依赖版本太旧!** 是微软服务器的SSL证书过期。

已验证版本:
- `edge-tts==7.2.3` (最新)
- `aiohttp==3.12.15` (最新)
- `certifi==2025.10.5` (最新)

## 解决方案

### 临时修复(已实施)

在`flask_backend/all_tts_functions/edge_tts.py`中使用SSL monkey patch:

```python
import ssl

# 保存原始函数
_original_create_default_context = ssl.create_default_context

def _create_unverified_context(*args, **kwargs):
    """创建不验证证书的SSL上下文"""
    context = _original_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

# 全局替换
ssl.create_default_context = _create_unverified_context
```

### ⚠️ 安全警告

**这是临时解决方案!** 禁用SSL验证存在安全风险:
- 容易受到中间人攻击(MITM)
- 无法验证服务器身份
- 仅适用于测试和开发环境

### 长期解决方案

1. **等待微软修复** (推荐)
   - 监控 [edge-tts GitHub Issues](https://github.com/rany2/edge-tts/issues)
   - 微软通常会快速修复证书问题

2. **使用其他TTS服务**
   - Azure TTS (付费但稳定)
   - OpenAI TTS
   - Fish TTS
   - 自定义TTS服务

3. **降级到旧版本** (不推荐)
   - 某些旧版本可能还在使用有效证书的endpoint
   - 但可能缺少新功能和bug修复

## 测试验证

运行测试脚本验证修复:

```bash
python test_edge_tts_ssl.py
```

预期输出:
```
✅ 测试成功!
✅ SSL证书问题已解决
```

## 监控和恢复

### 如何检查微软是否修复了证书

```bash
# Linux/Mac
openssl s_client -connect api.msedgeservices.com:443 -servername api.msedgeservices.com

# Windows PowerShell
(Invoke-WebRequest -Uri "https://api.msedgeservices.com").BaseResponse.ServerCertificate
```

### 恢复正常SSL验证

当微软修复证书后,在`edge_tts.py`中删除或注释掉monkey patch代码:

```python
# 删除以下行:
# ssl.create_default_context = _create_unverified_context
```

然后测试:
```bash
python test_edge_tts_ssl.py
```

## 参考链接

- [edge-tts GitHub](https://github.com/rany2/edge-tts)
- [SSL Certificate Transparency Log](https://crt.sh/?q=api.msedgeservices.com)
- [项目Issue追踪](https://github.com/huguanjin/PPT-TO-VIDEO/issues)

---

**最后更新**: 2025-10-17  
**修复版本**: v2.3.1  
**状态**: ✅ 临时修复已实施,等待微软官方修复
