import { Injectable } from '@nestjs/common';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

@Injectable()
export class UploadService {
  private supabase: SupabaseClient | null = null;

  constructor() {
    const url = process.env.SUPABASE_URL;
    const key = process.env.SUPABASE_SERVICE_KEY;
    if (url && key && key !== 'your-supabase-service-role-key') {
      this.supabase = createClient(url, key);
    } else {
      console.warn('[UploadService] ⚠️ Supabase Storage not configured. Video upload disabled.');
    }
  }

  async uploadVideo(file: Express.Multer.File): Promise<string | null> {
    if (!this.supabase) {
      console.warn('[UploadService] Upload skipped - Supabase not configured');
      return null;
    }

    const fileName = `accidents/${Date.now()}_${file.originalname}`;
    const { error } = await this.supabase.storage
      .from('videos')
      .upload(fileName, file.buffer, { contentType: file.mimetype });

    if (error) {
      console.error('[Upload] Failed:', error.message);
      return null;
    }

    const { data } = this.supabase.storage.from('videos').getPublicUrl(fileName);
    return data.publicUrl;
  }
}
