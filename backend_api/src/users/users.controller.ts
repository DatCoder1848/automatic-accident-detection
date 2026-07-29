import { Controller, Get, Post, Patch, Param, Body, UseGuards } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBody, ApiBearerAuth } from '@nestjs/swagger';
import { UsersService } from './users.service.js';
import { JwtAuthGuard } from '../auth/jwt-auth.guard.js';
import { Prisma } from '@prisma/client'; //from '../../generated/prisma/client.js';

@ApiTags('Users')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard)
@Controller('users')
export class UsersController {
  constructor(private usersService: UsersService) {}

  @Get()
  @ApiOperation({ summary: 'List all users' })
  findAll() {
    return this.usersService.findAll();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get user by ID' })
  findOne(@Param('id') id: string) {
    return this.usersService.findOne(id);
  }

  @Post()
  @ApiOperation({ summary: 'Create a new user' })
  @ApiBody({ schema: { properties: { email: { type: 'string' }, password: { type: 'string' }, name: { type: 'string' }, role: { type: 'string', enum: ['ADMIN', 'OPERATOR', 'VIEWER'] } }, required: ['email', 'password'] } })
  create(@Body() data: { email: string; password: string; name?: string; role?: string }) {
    return this.usersService.create(data);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update user info' })
  update(@Param('id') id: string, @Body() data: { email?: string; name?: string; role?: string }) {
    return this.usersService.update(id, data);
  }
}
