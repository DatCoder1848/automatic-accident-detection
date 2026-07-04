import { Module } from '@nestjs/common';
import { CamerasController } from './cameras.controller.js';
import { CamerasService } from './cameras.service.js';

@Module({
  controllers: [CamerasController],
  providers: [CamerasService],
})
export class CamerasModule {}
