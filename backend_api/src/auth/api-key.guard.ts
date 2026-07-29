import { Injectable, CanActivate, ExecutionContext, UnauthorizedException } from '@nestjs/common';

@Injectable()
export class ApiKeyGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-api-key'];
    const validKey = process.env.AI_SERVICE_API_KEY || 'ai-service-secret-key';

    if (apiKey === validKey) return true;
    throw new UnauthorizedException('Invalid API key');
  }
}
