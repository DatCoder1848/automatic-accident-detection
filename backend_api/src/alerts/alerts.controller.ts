import { Controller, Get, Param, Patch, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiBearerAuth } from '@nestjs/swagger';
import { AlertsService } from './alerts.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';

@ApiTags('Alerts')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('alerts')
export class AlertsController {
  constructor(private alertsService: AlertsService) {}

  @Get()
  @ApiOperation({ summary: 'Get alerts for a user' })
  @ApiQuery({ name: 'userId', required: false, description: 'Filter by user ID' })
  findByUser(@Query('userId') userId: string) {
    return this.alertsService.findByUser(userId);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get alert by ID' })
  findOne(@Param('id') id: string) {
    return this.alertsService.findOne(id);
  }

  @Patch(':id/read')
  @ApiOperation({ summary: 'Mark alert as read' })
  markAsRead(@Param('id') id: string) {
    return this.alertsService.markAsRead(id);
  }
}
