import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';
import { CamerasModule } from './cameras/cameras.module';
import { AccidentsModule } from './accidents/accidents.module';
import { AlertsModule } from './alerts/alerts.module';

@Module({
  imports: [PrismaModule, AuthModule, UsersModule, CamerasModule, AlertsModule, AccidentsModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
