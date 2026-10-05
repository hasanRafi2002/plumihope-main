import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }
                .tag(0)

            ExploreView(isActive: selectedTab == 1)
                .tabItem {
                    Label("Discover", systemImage: "magnifyingglass")
                }
                .tag(1)

            HelpRequestStartView()
                .tabItem {
                    Label("Request Help", systemImage: "hand.raised")
                }
                .tag(2)

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.circle")
                }
                .tag(3)
        }
    }
}

#Preview {
    MainTabView()
        .environmentObject(AuthManager.shared)
}
