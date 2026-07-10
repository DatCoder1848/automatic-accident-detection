import { Module } from '@nestjs/common';
import { AppController } from './app.controller.js';
import { AppService } from './app.service.js';
import { PrismaModule } from './prisma/prisma.module.js';
import { AuthModule } from './auth/auth.module.js';
import { UsersModule } from './users/users.module.js';
import { CamerasModule } from './cameras/cameras.module.js';
import { AccidentsModule } from './accidents/accidents.module.js';
import { AlertsModule } from './alerts/alerts.module.js';
import { EventsModule } from './events/events.module.js';
import { UploadModule } from './upload/upload.module.js';

@Module({
  imports: [PrismaModule, EventsModule, AuthModule, UsersModule, CamerasModule, AlertsModule, AccidentsModule, UploadModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
