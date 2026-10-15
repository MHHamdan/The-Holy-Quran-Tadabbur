import { HubPage } from '../components/layout/HubPage';
import { MoreContent } from '../components/layout/MoreContent';

/** Full-page version of the More sheet (deep links, desktop). */
export function MorePage() {
  return (
    <HubPage titleKey="hub_more_title" subtitleKey="hub_more_subtitle">
      <MoreContent />
    </HubPage>
  );
}

export default MorePage;
