import { Injectable } from '@nestjs/common';
import { createClient } from '@supabase/supabase-js';

@Injectable()
export class UploadService {
  private supabase;

  constructor() {
    this.supabase = createClient(
      process.env.SUPABASE_URL || '',
      process.env.SUPABASE_SERVICE_KEY || '',
    );
  }

  async uploadVideo(file: Express.Multer.File): Promise<string | null> {
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
