import { Controller, Get, Post, Patch, Param, Body, Query, UseGuards } from '@nestjs/common';
import { AccidentsService } from './accidents.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

@UseGuards(JwtAuthGuard)
@Controller('accidents')
export class AccidentsController {
  constructor(private accidentsService: AccidentsService) {}

  @Post()
  create(@Body() data: any) {
    return this.accidentsService.create(data);
  }

  @Get()
  findAll(
    @Query('severity') severity?: string,
    @Query('status') status?: string,
    @Query('cameraId') cameraId?: string,
  ) {
    return this.accidentsService.findAll({ severity, status, cameraId });
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.accidentsService.findOne(id);
  }

  @Patch(':id')
  updateStatus(@Param('id') id: string, @Body() body: { status: string }) {
    return this.accidentsService.updateStatus(id, body.status);
  }
}
