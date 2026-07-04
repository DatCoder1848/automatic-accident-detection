import { Controller, Get, Post, Patch, Delete, Param, Query, Body, UseGuards } from '@nestjs/common';
import { CamerasService } from './cameras.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { JwtOrApiKeyGuard } from '../auth/jwt-or-apikey.guard.js';

@Controller('cameras')
export class CamerasController {
  constructor(private readonly camerasService: CamerasService) {}

  @Get()
  @UseGuards(JwtOrApiKeyGuard)
  findAll(@Query('status') status?: string) {
    return this.camerasService.findAll(status);
  }

  @Get(':id')
  @UseGuards(JwtOrApiKeyGuard)
  findOne(@Param('id') id: string) {
    return this.camerasService.findOne(id);
  }

  @Post()
  @UseGuards(JwtAuthGuard)
  create(@Body() data: { name: string; location: string; streamUrl: string; status?: string }) {
    return this.camerasService.create(data);
  }

  @Patch(':id')
  @UseGuards(JwtAuthGuard)
  update(@Param('id') id: string, @Body() data: { name?: string; location?: string; streamUrl?: string; status?: string }) {
    return this.camerasService.update(id, data);
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard)
  remove(@Param('id') id: string) {
    return this.camerasService.remove(id);
  }
}
