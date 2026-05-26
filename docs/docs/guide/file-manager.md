# 文件管理

ZgAdmin 内置文件管理模块，支持上传、预览、下载、重命名、删除等操作，并提供存储统计。

## 功能概览

- 单文件上传 / 批量上传
- 文件列表（按文件名、类型筛选）
- 图片预览（弹窗）
- 签名 URL 下载（支持非图片文件）
- 重命名
- 单条删除 / 批量删除
- 存储统计（已用空间、文件数量）

## 文件分类

系统根据扩展名自动分类：

| 分类 | 包含格式 |
|------|---------|
| image | jpg、jpeg、png、gif、webp、svg、bmp、ico |
| document | pdf、doc、docx、xls、xlsx、ppt、pptx、txt、md、csv、rtf |
| video | mp4、avi、mov、wmv、flv、mkv、webm |
| audio | mp3、wav、ogg、flac、aac、wma |
| other | 以上之外的格式 |

## 上传安全

| 安全项 | 说明 |
|--------|------|
| 扩展名白名单 | 仅允许预定义的扩展名上传 |
| 文件大小限制 | 由 `MAX_UPLOAD_SIZE` 环境变量控制，默认 10 MB |
| MIME 检测 | 验证文件实际 MIME 类型与扩展名是否匹配 |

## 存储路径

上传的文件按以下规则存储：

```
backend/static/uploads/{YYYY}/{MM}/{uuid}.{ext}
```

示例：`backend/static/uploads/2026/05/a1b2c3d4-e5f6-7890-abcd-ef1234567890.png`

## 后端 API

所有接口前缀：`/api/v1/resource/file`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/list` | 分页查询文件列表 |
| POST | `/upload` | 单文件上传（multipart/form-data） |
| POST | `/upload/batch` | 批量上传（multipart/form-data） |
| POST | `/update` | 更新文件信息（重命名） |
| POST | `/delete` | 删除文件（传 ID 数组） |
| GET | `/preview/{id}` | 预览文件（返回 Blob） |
| GET | `/signed-url/{id}` | 获取签名下载 URL |
| GET | `/stats` | 获取存储统计 |

### 请求示例

**上传单文件**

```
POST /api/v1/resource/file/upload
Content-Type: multipart/form-data

file: <binary>
```

**批量上传**

```
POST /api/v1/resource/file/upload/batch
Content-Type: multipart/form-data

files: <binary>  (可传多个)
```

**重命名**

```json
POST /api/v1/resource/file/update
{
  "id": "uuid",
  "name": "新文件名.pdf"
}
```

**存储统计响应**

```json
{
  "success": true,
  "data": {
    "total_files": 42,
    "total_size": 1073741824,
    "total_size_display": "1.00 GB",
    "by_type": {
      "image": { "count": 20, "size": 536870912 },
      "document": { "count": 15, "size": 322122547 },
      "other": { "count": 7, "size": 214748365 }
    }
  }
}
```

## 前端使用

路径：`资源管理 → 文件管理`（`/resource/file`）

功能：
- 按文件名、类型筛选
- 上传按钮（单文件）+ 批量上传
- 操作列：预览、下载、重命名、删除
- 批量选择删除
- 图片预览弹窗
- 非图片文件点击预览时自动触发下载

## 自定义配置

### 修改上传大小限制

编辑 `.env`：

```bash
MAX_UPLOAD_SIZE=10485760  # 10MB，单位字节
```

### 修改允许的扩展名

编辑 `backend/app/utils/file_upload.py` 中的 `ALLOWED_EXTENSIONS` 集合。

### 修改存储路径

编辑 `backend/app/utils/file_upload.py` 中的 `UPLOAD_DIR` 常量，默认为 `backend/static/uploads`。
