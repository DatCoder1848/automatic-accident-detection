import { Module } from '@nestjs/common';
import { AccidentsController } from './accidents.controller';
import { AccidentsService } from './accidents.service';
import { AlertsModule } from '../alerts/alerts.module';

@Module({
  imports: [AlertsModule],
  controllers: [AccidentsController],
  providers: [AccidentsService],
})
export class AccidentsModule {}
