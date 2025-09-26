"""
下载PPTist模板封面图片的脚本
"""
import os
import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_template_images():
    """下载模板封面图片"""
    
    # 图片URL和本地路径
    template_images = {
        'template_1.jpg': 'https://asset.pptist.cn/img/template_1.jpg',
        'template_2.jpg': 'https://asset.pptist.cn/img/template_2.jpg', 
        'template_3.jpg': 'https://asset.pptist.cn/img/template_3.jpg',
        'template_4.jpg': 'https://asset.pptist.cn/img/template_4.jpg'
    }
    
    # 目标目录
    img_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
    os.makedirs(img_dir, exist_ok=True)
    
    logger.info(f"开始下载模板图片到目录: {img_dir}")
    
    success_count = 0
    failed_count = 0
    
    for filename, url in template_images.items():
        try:
            local_path = os.path.join(img_dir, filename)
            
            # 如果文件已存在，跳过
            if os.path.exists(local_path):
                logger.info(f"✅ {filename} 已存在，跳过下载")
                success_count += 1
                continue
            
            logger.info(f"📥 正在下载: {filename}")
            
            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存到本地
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ {filename} 下载成功")
            success_count += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {filename} 下载失败: {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"❌ {filename} 保存失败: {e}")
            failed_count += 1
    
    logger.info(f"🎯 下载完成! 成功: {success_count}, 失败: {failed_count}")
    
    return success_count, failed_count

if __name__ == "__main__":
    download_template_images()