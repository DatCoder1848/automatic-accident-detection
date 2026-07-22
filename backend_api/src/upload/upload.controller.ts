import { Controller, Post, UseInterceptors, UploadedFile, UseGuards, Body } from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiTags, ApiOperation, ApiConsumes, ApiBody, ApiSecurity, ApiResponse } from '@nestjs/swagger';
import { UploadService } from './upload.service.js';
import { ApiKeyGuard } from '../auth/api-key.guard.js';
import { PrismaService } from '../prisma/prisma.service.js';
import { EventsGateway } from '../events/events.gateway.js';

@ApiTags('Upload')
@Controller('upload')
export class UploadController {
  constructor(
    private uploadService: UploadService,
    private prisma: PrismaService,
    private eventsGateway: EventsGateway,
  ) {}

  @Post('video')
  @UseGuards(ApiKeyGuard)
  @ApiSecurity('api-key')
  @ApiOperation({ summary: 'Upload accident video evidence (called by AI Engine after detection)' })
  @ApiConsumes('multipart/form-data')
  @ApiBody({ schema: { type: 'object', properties: { file: { type: 'string', format: 'binary' }, accidentId: { type: 'string', description: 'UUID of the accident to link video to' } }, required: ['file', 'accidentId'] } })
  @ApiResponse({ status: 201, description: 'Video uploaded, accident record updated, socket emitted' })
  @UseInterceptors(FileInterceptor('file'))
  async uploadVideo(
    @UploadedFile() file: Express.Multer.File,
    @Body('accidentId') accidentId: string,
  ) {
    const url = await this.uploadService.uploadVideo(file);
    if (!url) return { error: 'Upload failed' };

    if (accidentId) {
      await this.prisma.accident.update({
        where: { id: accidentId },
        data: { videoClipUrl: url },
      });
      this.eventsGateway.emitVideoReady({ accidentId, videoClipUrl: url });
    }

    return { url, accidentId };
  }
}
