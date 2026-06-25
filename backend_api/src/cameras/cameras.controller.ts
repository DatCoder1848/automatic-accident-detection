import { Controller, Get, Post, Patch, Delete, Param, Query, Body } from '@nestjs/common';
import { CamerasService } from './cameras.service';
import { CameraStatus } from '../../generated/prisma/client.js';

@Controller('cameras')
export class CamerasController {
  constructor(private readonly camerasService: CamerasService) {}

  @Get()
  findAll(@Query('status') status?: CameraStatus) {
    return this.camerasService.findAll(status);
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.camerasService.findOne(id);
  }

  @Post()
  create(@Body() data: { name: string; location: string; streamUrl: string; status?: CameraStatus }) {
    return this.camerasService.create(data);
  }

  @Patch(':id')
  update(@Param('id') id: string, @Body() data: { name?: string; location?: string; streamUrl?: string; status?: CameraStatus }) {
    return this.camerasService.update(id, data);
  }

  @Delete(':id')
  remove(@Param('id') id: string) {
    return this.camerasService.remove(id);
  }
}
