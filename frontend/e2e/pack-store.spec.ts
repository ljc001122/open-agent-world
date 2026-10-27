import { expect, test } from '@playwright/test';
import type { StorePack } from '../src/types/packs';

test('Store renders procedural Pack surfaces and reviews a version before installation', async ({ page, request }, testInfo) => {
  const profile = await (await request.get('/api/application')).json();
  await request.patch('/api/application/preferences', { data: {
    profile_id: profile.profile_id, generation: profile.generation,
    changes: { 'oaw-onboarding-v1': JSON.stringify({ version: 1, state: { status: 'skipped' } }), 'oaw.locale': 'en' },
  } });
  const packs: StorePack[] = ['standard', 'premium', 'paper', 'collector'].map(packaging => ({
    id: `preview.${packaging}`, name: `${packaging} Pack`, summary: 'A collection of possibilities.', description: 'Store preview fixture.',
    latest_version: '1.0.0', available_version: '1.0.0', installed_version: null, loaded_version: null,
    can_install: true, update_available: false, restart_required: false,
    preview: { packaging: packaging as NonNullable<StorePack['preview']>['packaging'], count: 3 },
  }));
  const mutations: string[] = [], errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/store/packs**', route => {
    const req = route.request(), path = new URL(req.url()).pathname;
    if (req.method() !== 'GET') mutations.push(path);
    const pack = packs.find(pack => path.startsWith(`/api/store/packs/${pack.id}`));
    if (!pack) return route.fulfill({ json: { items: packs, next_cursor: null } });
    if (path.includes('/versions/')) return route.fulfill({ json: {
      ...pack, pack_id: pack.id, version: '1.0.0', preview: { packaging: 'collector', count: 3 },
      manifest: { id: pack.id, version: '1.0.0', compatibility: { oaw: '>=0.1.0' },
        dependencies: { packs: [] }, runtime: { sandbox: { python: [] } } },
    } });
    return route.fulfill({ json: { ...pack, versions: ['1.0.0'], versions_next_cursor: null } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Open Pack and Card Library' }).click();
  const library = page.getByRole('dialog', { name: 'Pack & Card Library' });
  await library.getByRole('button', { name: 'Store', exact: true }).click();
  for (const pack of packs) {
    const surface = library.locator(`[data-pack-id="${pack.id}"]`);
    await surface.scrollIntoViewIfNeeded();
    await expect(surface).toHaveAttribute('data-renderer', 'webgl', { timeout: 15000 });
    await expect(surface).toHaveAttribute('data-packaging', pack.preview!.packaging);
  }
  await page.screenshot({ path: testInfo.outputPath('store-procedural-packs.png') });
  const premium = library.locator('[data-pack-id="preview.premium"]');
  const touch = premium.getByRole('button', { name: 'View premium Pack details' });
  await touch.focus();
  await touch.press('ArrowRight');
  await expect(premium.locator('canvas')).toHaveAttribute('data-yaw', '8.0');
  await touch.press('Enter');
  await expect(library.locator('.store-detail .library-pack')).toHaveAttribute('data-packaging', 'collector');
  await expect(library.locator('.store-detail .library-pack')).toHaveAttribute('data-renderer', 'webgl');
  await expect(library.getByRole('button', { name: 'Get', exact: true })).toBeEnabled();
  expect(mutations).toEqual([]);
  await library.getByRole('button', { name: 'Back to Store' }).click();
  await expect(library.locator('[data-pack-id="preview.premium"]')).toHaveAttribute('data-packaging', 'premium');
  expect(errors).toEqual([]);
});
