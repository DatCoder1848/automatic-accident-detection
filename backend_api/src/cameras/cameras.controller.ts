import { Controller, Get, Post, Patch, Delete, Param, Query, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiQuery, ApiBearerAuth, ApiSecurity } from '@nestjs/swagger';
import { CamerasService } from './cameras.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { JwtOrApiKeyGuard } from '../auth/jwt-or-apikey.guard.js';

@ApiTags('Cameras')
@Controller('cameras')
export class CamerasController {
  constructor(private readonly camerasService: CamerasService) {}

  @Get()
  @UseGuards(JwtOrApiKeyGuard)
  @ApiBearerAuth()
  @ApiSecurity('api-key')
  @ApiOperation({ summary: 'List all cameras (optional filter by status)' })
  @ApiQuery({ name: 'status', required: false, enum: ['ACTIVE', 'INACTIVE', 'MAINTENANCE'] })
  findAll(@Query('status') status?: string) {
    return this.camerasService.findAll(status);
  }

  @Get(':id')
  @UseGuards(JwtOrApiKeyGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get camera by ID' })
  findOne(@Param('id') id: string) {
    return this.camerasService.findOne(id);
  }

  @Post()
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create a new camera' })
  @ApiBody({ schema: { properties: { name: { type: 'string' }, location: { type: 'string' }, streamUrl: { type: 'string' }, status: { type: 'string', enum: ['ACTIVE', 'INACTIVE', 'MAINTENANCE'] } }, required: ['name', 'location', 'streamUrl'] } })
  create(@Body() data: { name: string; location: string; streamUrl: string; status?: string }) {
    return this.camerasService.create(data);
  }

  @Patch(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update camera info' })
  update(@Param('id') id: string, @Body() data: { name?: string; location?: string; streamUrl?: string; status?: string }) {
    return this.camerasService.update(id, data);
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete a camera' })
  remove(@Param('id') id: string) {
    return this.camerasService.remove(id);
  }
}
