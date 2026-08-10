import 'dotenv/config';
import { PrismaClient } from '../generated/prisma/client.js';
import { PrismaPg } from '@prisma/adapter-pg';
import * as bcrypt from 'bcrypt';

const adapter = new PrismaPg(process.env.DIRECT_URL || process.env.DATABASE_URL!);
const prisma = new PrismaClient({ adapter });

const cameras = [
  { name: "CAM_CRASH_1", location: "Crash Zone 1", streamUrl: "../data_storage/video_clips/positive/crash_1.mp4", aiConfig: { src_pts: [[432,61],[541,561],[1015,511],[750,59]], pixel_to_meter: 0.05, bev_width: 150, bev_height: 250, horizon_y: 50, y_split: 150, thresh_near: -4.0, thresh_far: -35.0, dist_thresh: 3.0 }},
  { name: "CAM_CRASH_2", location: "Crash Zone 2", streamUrl: "../data_storage/video_clips/positive/crash_2.mp4", aiConfig: { src_pts: [[357,266],[678,241],[721,482],[261,491]], pixel_to_meter: 0.02, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0, dist_thresh: 3.0 }},
  { name: "CAM_CRASH_3", location: "Crash Zone 3", streamUrl: "../data_storage/video_clips/positive/crash_3.mp4", aiConfig: { src_pts: [[508,296],[817,280],[937,452],[515,493]], pixel_to_meter: 0.02, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -5.0, thresh_far: -6.0, dist_thresh: 3.0 }},
  { name: "CAM_CRASH_4", location: "Crash Zone 4", streamUrl: "../data_storage/video_clips/positive/crash_4.mp4", aiConfig: { src_pts: [[325,191],[574,182],[934,517],[550,539]], pixel_to_meter: 0.05, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0, dist_thresh: 3.0, validation_max_v: 4.5, require_stuck_vehicle: false }},
  { name: "CAM_CRASH_5", location: "Crash Zone 5", streamUrl: "../data_storage/video_clips/positive/crash_5.mp4", aiConfig: { src_pts: [[325,191],[574,182],[934,517],[550,539]], pixel_to_meter: 0.05, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0, dist_thresh: 3.0, validation_max_v: 4.5, require_stuck_vehicle: false }},
  { name: "CAM_CRASH_6", location: "Crash Zone 6", streamUrl: "../data_storage/video_clips/positive/crash_6.mp4", aiConfig: { src_pts: [[460,183],[665,159],[915,458],[572,504]], pixel_to_meter: 0.05, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0, dist_thresh: 3.0, validation_max_v: 4.5, require_stuck_vehicle: false }},
  { name: "CAM_CRASH_7", location: "Crash Zone 7", streamUrl: "../data_storage/video_clips/positive/crash_7_CP2.mp4", aiConfig: { src_pts: [[403,199],[852,209],[770,554],[77,397]], pixel_to_meter: 0.02, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -4.0, thresh_far: -7.0, dist_thresh: 3.0 }},
  { name: "CAM_CRASH_8", location: "Crash Zone 8", streamUrl: "../data_storage/video_clips/positive/crash_8.mp4", aiConfig: { src_pts: [[99,167],[181,161],[207,214],[71,222]], pixel_to_meter: 0.06, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_CRASH_9", location: "Crash Zone 9", streamUrl: "../data_storage/video_clips/positive/crash_9.mp4", aiConfig: { src_pts: [[448,382],[572,377],[631,454],[441,484]], pixel_to_meter: 0.01, bev_width: 320, bev_height: 400, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_CRASH_10", location: "Crash Zone 10", streamUrl: "../data_storage/video_clips/positive/crash_10.mp4", aiConfig: { src_pts: [[483,372],[760,397],[637,498],[201,433]], pixel_to_meter: 0.01, bev_width: 320, bev_height: 400, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_CRASH_11", location: "Crash Zone 11", streamUrl: "../data_storage/video_clips/positive/crash_11.mp4", aiConfig: { src_pts: [[326,307],[441,401],[255,490],[174,376]], pixel_to_meter: 0.02, bev_width: 200, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_CRASH_12", location: "Crash Zone 12", streamUrl: "../data_storage/video_clips/positive/crash_12.mp4", aiConfig: { src_pts: [[326,307],[441,401],[255,490],[174,376]], pixel_to_meter: 0.02, bev_width: 200, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0, require_stuck_vehicle: false }},
  { name: "CAM_NOR_1", location: "Normal Zone 1", streamUrl: "../data_storage/video_clips/negative/normal_1.mp4", aiConfig: { src_pts: [[271,363],[365,362],[293,467],[156,462]], pixel_to_meter: 0.035, bev_width: 150, bev_height: 250, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_2", location: "Normal Zone 2", streamUrl: "../data_storage/video_clips/negative/normal_2.mp4", aiConfig: { src_pts: [[340,273],[658,269],[665,327],[298,334]], pixel_to_meter: 0.02, bev_width: 220, bev_height: 150, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_3", location: "Normal Zone 3", streamUrl: "../data_storage/video_clips/negative/normal_3.mp4", aiConfig: { src_pts: [[373,345],[739,348],[746,380],[360,377]], pixel_to_meter: 0.02, bev_width: 220, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_4", location: "Normal Zone 4", streamUrl: "../data_storage/video_clips/negative/normal_4.mp4", aiConfig: { src_pts: [[373,345],[739,348],[746,380],[360,377]], pixel_to_meter: 0.02, bev_width: 220, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_5", location: "Normal Zone 5", streamUrl: "../data_storage/video_clips/negative/normal_5.mp4", aiConfig: { src_pts: [[373,345],[739,348],[746,380],[360,377]], pixel_to_meter: 0.02, bev_width: 220, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_6", location: "Normal Zone 6", streamUrl: "../data_storage/video_clips/negative/normal_6.mp4", aiConfig: { src_pts: [[384,191],[696,181],[904,401],[341,534]], pixel_to_meter: 0.05, bev_width: 200, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_7", location: "Normal Zone 7", streamUrl: "../data_storage/video_clips/negative/normal_7.mp4", aiConfig: { src_pts: [[384,191],[696,181],[904,401],[341,534]], pixel_to_meter: 0.05, bev_width: 200, bev_height: 200, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_8", location: "Normal Zone 8", streamUrl: "../data_storage/video_clips/negative/normal_8.mp4", aiConfig: { src_pts: [[360,181],[602,128],[839,285],[512,535]], pixel_to_meter: 0.05, bev_width: 300, bev_height: 300, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
  { name: "CAM_NOR_9", location: "Normal Zone 9", streamUrl: "../data_storage/video_clips/negative/normal_9.mp4", aiConfig: { src_pts: [[360,181],[602,128],[839,285],[512,535]], pixel_to_meter: 0.05, bev_width: 300, bev_height: 300, horizon_y: 200, y_split: 400, thresh_near: -6.0, thresh_far: -9.0 }},
];

async function main() {
  const hash = (pw: string) => bcrypt.hashSync(pw, 10);

  // Users
  await prisma.user.upsert({
    where: { email: 'admin@system.com' },
    update: {},
    create: { email: 'admin@system.com', password: hash('admin123'), name: 'Admin', role: 'ADMIN' },
  });
  await prisma.user.upsert({
    where: { email: 'operator@system.com' },
    update: {},
    create: { email: 'operator@system.com', password: hash('operator123'), name: 'Operator', role: 'OPERATOR' },
  });

  // Clean up old data (respect FK constraints)
  await prisma.alert.deleteMany({});
  await prisma.accident.deleteMany({});
  await prisma.camera.deleteMany({});
  await prisma.camera.createMany({ data: cameras as any });

  const count = await prisma.camera.count();
  console.log(`Seed completed! ${count} cameras created.`);
}

main().catch(console.error).finally(() => prisma.$disconnect());
