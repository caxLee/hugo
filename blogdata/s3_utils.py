import os
import hashlib
import aioboto3
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Cloudflare R2 配置
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY', '3926e0aecd942e9ea45667eaff4095f6')
R2_SECRET_KEY = os.getenv('R2_SECRET_KEY', 'eb7520fc3e66534dc80f39beb7bc08153bc79bd2272f58a799e0ec0c26257256')
R2_ENDPOINT = os.getenv('R2_ENDPOINT', 'https://88a983a33ad1822518ad743ad7d98dcb.r2.cloudflarestorage.com')
R2_BUCKET = 'ainews'  # 固定的bucket名称
R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL', 'https://88a983a33ad1822518ad743ad7d98dcb.r2.cloudflarestorage.com/ainews')

class S3ImageUploader:
    def __init__(self):
        self.session = None
        self.s3_client = None
    
    async def __aenter__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY
        )
        self.s3_client = await self.session.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            region_name='auto'  # Cloudflare R2 使用 'auto'
        ).__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.s3_client:
            await self.s3_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def upload_image(self, image_data, file_path, content_type=None):
        """
        上传图片到S3/R2
        
        Args:
            image_data: 图片二进制数据
            file_path: S3中的文件路径 (例如: images/articles/2024-09-10/001.jpg)
            content_type: MIME类型 (可选)
        
        Returns:
            公开访问的URL字符串，如果失败返回None
        """
        try:
            # 如果没有指定content_type，根据文件扩展名推断
            if not content_type:
                ext = os.path.splitext(file_path)[1].lower()
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'image/jpeg')
            
            # 上传到S3/R2
            await self.s3_client.put_object(
                Bucket=R2_BUCKET,
                Key=file_path,
                Body=image_data,
                ContentType=content_type,
                CacheControl='public, max-age=31536000'  # 缓存1年
            )
            
            # 返回公开访问URL
            public_url = f"{R2_PUBLIC_URL}/{file_path}"
            return public_url
            
        except Exception as e:
            print(f"❌ S3上传失败: {str(e)}")
            return None
    
    async def check_image_exists(self, file_path):
        """
        检查S3中是否已存在指定路径的文件
        
        Args:
            file_path: S3中的文件路径
        
        Returns:
            如果存在返回公开URL，否则返回None
        """
        try:
            await self.s3_client.head_object(Bucket=R2_BUCKET, Key=file_path)
            return f"{R2_PUBLIC_URL}/{file_path}"
        except:
            return None

def get_file_extension_from_url_or_content_type(url, content_type=''):
    """从URL或Content-Type获取文件扩展名"""
    # 先尝试从URL获取
    parsed_url = urlparse(url)
    file_ext = os.path.splitext(parsed_url.path)[1]
    
    if file_ext and len(file_ext) <= 5:
        return file_ext
    
    # 如果URL没有有效扩展名，从Content-Type推断
    if 'jpeg' in content_type or 'jpg' in content_type: 
        return '.jpg'
    elif 'png' in content_type: 
        return '.png'
    elif 'gif' in content_type: 
        return '.gif'
    elif 'webp' in content_type: 
        return '.webp'
    else: 
        return '.jpg'  # 默认使用jpg

async def download_and_upload_image_to_s3(session, url, date_str, index, image_hashes):
    """
    下载图片并上传到S3，支持去重
    
    Args:
        session: aiohttp客户端session
        url: 图片URL
        date_str: 日期字符串 (例如: 2024-09-10)
        index: 图片序号
        image_hashes: 哈希字典，用于去重
    
    Returns:
        S3公开访问URL，如果失败返回None
    """
    try:
        # 检查URL是否已经处理过
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if url_hash in image_hashes:
            existing_url = image_hashes[url_hash]
            print(f"🔄 图片URL已处理过，使用缓存URL: {existing_url}")
            return existing_url

        # 下载图片
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ 下载图片失败，状态码: {response.status}, URL: {url}")
                return None
            
            image_data = await response.read()
            if not image_data:
                print(f"❌ 下载的图片数据为空, URL: {url}")
                return None

            # 计算图片内容哈希
            image_hash = hashlib.sha256(image_data).hexdigest()

            # 检查内容哈希是否已存在
            if image_hash in image_hashes:
                existing_url = image_hashes[image_hash]
                print(f"🔄 图片内容已存在 (内容哈希: {image_hash[:8]}...), 使用现有URL: {existing_url}")
                # 同时更新URL哈希记录
                image_hashes[url_hash] = existing_url
                return existing_url

            # 获取文件扩展名
            content_type = response.headers.get('Content-Type', '')
            file_ext = get_file_extension_from_url_or_content_type(url, content_type)

            # 构建S3文件路径
            filename = f"{index:03d}{file_ext}"
            s3_file_path = f"images/articles/{date_str}/{filename}"

            # 上传到S3
            async with S3ImageUploader() as uploader:
                # 先检查是否已存在
                existing_url = await uploader.check_image_exists(s3_file_path)
                if existing_url:
                    print(f"🔄 S3中已存在相同路径文件: {s3_file_path}")
                    image_hashes[url_hash] = existing_url
                    image_hashes[image_hash] = existing_url
                    return existing_url
                
                # 上传新文件
                public_url = await uploader.upload_image(image_data, s3_file_path, content_type)
                if public_url:
                    print(f"✅ 图片上传成功: {s3_file_path} -> {public_url}")
                    # 更新哈希记录
                    image_hashes[url_hash] = public_url
                    image_hashes[image_hash] = public_url
                    return public_url
                else:
                    print(f"❌ 图片上传失败: {s3_file_path}")
                    return None

    except Exception as e:
        print(f"❌ 处理图片时发生错误: {str(e)}, URL: {url}")
        return None 