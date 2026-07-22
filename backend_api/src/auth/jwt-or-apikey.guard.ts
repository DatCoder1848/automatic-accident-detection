import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { JwtAuthGuard } from './jwt-auth.guard.js';
import { ApiKeyGuard } from './api-key.guard.js';

@Injectable()
export class JwtOrApiKeyGuard implements CanActivate {
  private jwtGuard = new JwtAuthGuard();
  private apiKeyGuard = new ApiKeyGuard();

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();

    if (request.headers['x-api-key']) {
      return this.apiKeyGuard.canActivate(context);
    }

    try {
      return await this.jwtGuard.canActivate(context) as boolean;
    } catch {
      return false;
    }
  }
}
