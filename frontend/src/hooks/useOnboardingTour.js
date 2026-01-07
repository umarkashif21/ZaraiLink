import { useEffect, useRef, useCallback } from 'react';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';

const ONBOARDING_KEY = 'zarailink-onboarding-completed';


const useOnboardingTour = () => {
  const driverRef = useRef(null);

  const tourSteps = [
    {
      element: '.navbar-logo',
      popover: {
        title: 'Welcome to ZaraiLink!',
        description: 'Your comprehensive agricultural trade intelligence platform. Let\'s take a quick tour!',
        side: 'bottom',
      }
    },
    {
      element: '.nav-dropdown:first-of-type',
      popover: {
        title: 'Trade Directory',
        description: 'Find verified suppliers and buyers in the agricultural sector. Search by product, location, and more.',
        side: 'bottom',
      }
    },
    {
      element: '.nav-dropdown:last-of-type',
      popover: {
        title: 'Trade Intelligence',
        description: 'Access market analytics, trade ledger data, and AI-powered predictions.',
        side: 'bottom',
      }
    },
    {
      element: '.token-display',
      popover: {
        title: 'Your Tokens',
        description: 'Use tokens to unlock premium contact information. Purchase more in Subscription.',
        side: 'bottom',
      }
    },
    {
      element: '.theme-toggle',
      popover: {
        title: 'Dark Mode',
        description: 'Toggle between light and dark themes for comfortable viewing.',
        side: 'bottom',
      }
    },
    {
      element: '.user-menu',
      popover: {
        title: 'Your Account',
        description: 'Access your profile settings and sign out from here.',
        side: 'left',
      }
    },
  ];

  const startTour = useCallback(() => {
    if (driverRef.current) {
      driverRef.current.destroy();
    }

    driverRef.current = driver({
      showProgress: true,
      animate: true,
      allowClose: true,
      overlayClickNext: false,
      stagePadding: 10,
      stageRadius: 8,
      popoverClass: 'zarailink-driver-popover',
      steps: tourSteps,
      onDestroyStarted: () => {
        localStorage.setItem(ONBOARDING_KEY, 'true');
        driverRef.current?.destroy();
      },
    });

    driverRef.current.drive();
  }, []);

  const shouldShowTour = useCallback(() => {
    return !localStorage.getItem(ONBOARDING_KEY);
  }, []);

  const resetTour = useCallback(() => {
    localStorage.removeItem(ONBOARDING_KEY);
  }, []);

  
  useEffect(() => {
    const timer = setTimeout(() => {
      if (shouldShowTour()) {
        startTour();
      }
    }, 1500); 

    return () => {
      clearTimeout(timer);
      if (driverRef.current) {
        driverRef.current.destroy();
      }
    };
  }, [shouldShowTour, startTour]);

  return {
    startTour,
    shouldShowTour,
    resetTour,
  };
};

export default useOnboardingTour;
