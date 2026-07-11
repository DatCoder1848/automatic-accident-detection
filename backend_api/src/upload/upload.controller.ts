import { Controller, Post, UseInterceptors, UploadedFile, UseGuards, Body } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { UploadService } from './upload.service.js';
import { ApiKeyGuard } from '../auth/api-key.guard.js';
import { PrismaService } from '../prisma/prisma.service.js';
import { EventsGateway } from '../events/events.gateway.js';

@Controller('upload')
export class UploadController {
  constructor(
    private uploadService: UploadService,
    private prisma: PrismaService,
    private eventsGateway: EventsGateway,
  ) {}

  @Post('video')
  @UseGuards(ApiKeyGuard)
  @UseInterceptors(FileInterceptor('file'))
  async uploadVideo(
    @UploadedFile() file: Express.Multer.File,
    @Body('accidentId') accidentId: string,
  ) {
    // Upload to Supabase Storage
    const url = await this.uploadService.uploadVideo(file);
    if (!url) return { error: 'Upload failed' };

    // If accidentId provided, update the accident record with video URL
    if (accidentId) {
      await this.prisma.accident.update({
        where: { id: accidentId },
        data: { videoClipUrl: url },
      });
      // Emit socket event so frontend can load the video
      this.eventsGateway.emitVideoReady({ accidentId, videoClipUrl: url });
    }

    return { url, accidentId };
  }
}
