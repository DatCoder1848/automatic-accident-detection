import { Controller, Post, UseInterceptors, UploadedFile, UseGuards } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { UploadService } from './upload.service.js';
import { ApiKeyGuard } from '../auth/api-key.guard.js';

@Controller('upload')
export class UploadController {
  constructor(private uploadService: UploadService) {}

  @Post('video')
  @UseGuards(ApiKeyGuard)
  @UseInterceptors(FileInterceptor('file'))
  async uploadVideo(@UploadedFile() file: Express.Multer.File) {
    const url = await this.uploadService.uploadVideo(file);
    if (!url) return { error: 'Upload failed' };
    return { url };
  }
}
