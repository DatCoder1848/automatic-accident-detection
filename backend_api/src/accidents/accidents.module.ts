import { Module } from '@nestjs/common';
import { AccidentsController } from './accidents.controller.js';
import { AccidentsService } from './accidents.service.js';
import { AlertsModule } from '../alerts/alerts.module.js';

@Module({
  imports: [AlertsModule],
  controllers: [AccidentsController],
  providers: [AccidentsService],
})
export class AccidentsModule {}
