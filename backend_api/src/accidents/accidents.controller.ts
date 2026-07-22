import { Controller, Get, Post, Patch, Param, Body, Query, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiQuery, ApiResponse, ApiBearerAuth, ApiSecurity } from '@nestjs/swagger';
import { AccidentsService } from './accidents.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { ApiKeyGuard } from '../auth/api-key.guard.js';

@ApiTags('Accidents')
@Controller('accidents')
export class AccidentsController {
  constructor(private accidentsService: AccidentsService) {}

  @Post()
  @UseGuards(ApiKeyGuard)
  @ApiSecurity('api-key')
  @ApiOperation({ summary: 'Report a new accident (called by AI Engine)' })
  @ApiBody({ schema: { properties: { cameraId: { type: 'string' }, confidence: { type: 'number' }, severity: { type: 'string', enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] }, description: { type: 'string' }, latitude: { type: 'number' }, longitude: { type: 'number' } }, required: ['cameraId', 'confidence', 'severity'] } })
  @ApiResponse({ status: 201, description: 'Accident created, returns object with id' })
  create(@Body() data: any) {
    return this.accidentsService.create(data);
  }

  @Get()
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'List all accidents (with optional filters)' })
  @ApiQuery({ name: 'severity', required: false, enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] })
  @ApiQuery({ name: 'status', required: false, enum: ['PENDING', 'CONFIRMED', 'FALSE_ALARM', 'RESOLVED'] })
  @ApiQuery({ name: 'cameraId', required: false })
  findAll(
    @Query('severity') severity?: string,
    @Query('status') status?: string,
    @Query('cameraId') cameraId?: string,
  ) {
    return this.accidentsService.findAll({ severity, status, cameraId });
  }

  @Get(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get accident by ID' })
  findOne(@Param('id') id: string) {
    return this.accidentsService.findOne(id);
  }

  @Patch(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update accident status' })
  @ApiBody({ schema: { properties: { status: { type: 'string', enum: ['CONFIRMED', 'FALSE_ALARM', 'RESOLVED'] } } } })
  updateStatus(@Param('id') id: string, @Body() body: { status: string }) {
    return this.accidentsService.updateStatus(id, body.status);
  }
}
