interface FileItem {
  id: string;
  name: string;
  path: string;
  size: number;
  size_display: string;
  mime_type: string;
  file_type: string;
  extension: string;
  uploader_id: string;
  uploader_name: string;
  created_at: string;
}

interface FileFilter {
  name: string | null;
  file_type: string | null;
}

export type { FileItem, FileFilter };
