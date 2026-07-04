import { Controller, Get, Post, Patch, Param, Body, Query, UseGuards } from '@nestjs/common';
import { AccidentsService } from './accidents.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { ApiKeyGuard } from '../auth/api-key.guard.js';

@Controller('accidents')
export class AccidentsController {
  constructor(private accidentsService: AccidentsService) {}

  @Post()
  @UseGuards(ApiKeyGuard)
  create(@Body() data: any) {
    return this.accidentsService.create(data);
  }

  @Get()
  @UseGuards(JwtAuthGuard)
  findAll(
    @Query('severity') severity?: string,
    @Query('status') status?: string,
    @Query('cameraId') cameraId?: string,
  ) {
    return this.accidentsService.findAll({ severity, status, cameraId });
  }

  @Get(':id')
  @UseGuards(JwtAuthGuard)
  findOne(@Param('id') id: string) {
    return this.accidentsService.findOne(id);
  }

  @Patch(':id')
  @UseGuards(JwtAuthGuard)
  updateStatus(@Param('id') id: string, @Body() body: { status: string }) {
    return this.accidentsService.updateStatus(id, body.status);
  }
}
