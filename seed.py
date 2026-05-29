from partners.models import Partner, PartnerEvent, PartnerAd
from datetime import date

partners = list(Partner.objects.all())

for partner in partners:
    print(f"\n✅ {partner.company_name}")
    PartnerEvent.objects.create(partner=partner, title="Summer Music Festival", title_en="Summer Music Festival", title_fr="Festival de Musique d'Ete", description="A spectacular outdoor music festival.", description_en="A spectacular outdoor music festival.", description_fr="Un festival de musique en plein air.", start_date=date(2026, 6, 15), end_date=date(2026, 6, 17), event_time="20:00", price=15.000, status="approved", is_published=True, is_boosted=False)
    print("  Event 1 cree")
    PartnerEvent.objects.create(partner=partner, title="Business Networking Night", title_en="Business Networking Night", title_fr="Soiree Networking Business", description="Connect with professionals.", description_en="Connect with professionals.", description_fr="Rencontrez des professionnels.", start_date=date(2026, 6, 25), end_date=date(2026, 6, 25), event_time="18:30", price=0.000, status="approved", is_published=True, is_boosted=False)
    print("  Event 2 cree")
    PartnerAd.objects.create(partner=partner, title="Summer Sale", destination_link="https://example.com/summer-sale", start_date=date(2026, 6, 1), end_date=date(2026, 6, 30), status="active")
    print("  Ad 1 creee")
    PartnerAd.objects.create(partner=partner, title="Grand Opening", destination_link="https://example.com/opening", start_date=date(2026, 7, 1), end_date=date(2026, 7, 15), status="active")
    print("  Ad 2 creee")

print("\nTermine !")
print("Events total :", PartnerEvent.objects.count())
print("Ads total :", PartnerAd.objects.count())